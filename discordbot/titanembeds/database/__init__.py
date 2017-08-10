from contextlib import contextmanager
from asyncio_extras import threadpool
import sqlalchemy as db
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

import json
import discord
import time

Base = declarative_base()

from titanembeds.database.guilds import Guilds
from titanembeds.database.messages import Messages
from titanembeds.database.guild_members import GuildMembers
from titanembeds.database.unauthenticated_users import UnauthenticatedUsers
from titanembeds.database.unauthenticated_bans import UnauthenticatedBans
from titanembeds.database.keyvalue_properties import KeyValueProperties

class DatabaseInterface(object):
    # Courtesy of https://github.com/SunDwarf/Jokusoramame
    def __init__(self, bot):
        self.bot = bot

        self.engine = None  # type: Engine
        self._sessionmaker = None  # type: sessionmaker

    async def connect(self, dburi):
        async with threadpool():
            self.engine = create_engine(dburi, pool_recycle=10)
            self._sessionmaker = sessionmaker(bind=self.engine, expire_on_commit=False)

    @contextmanager
    def get_session(self) -> Session:
        session = self._sessionmaker()  # type: Session
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    async def push_message(self, message):
        if message.server:
            async with threadpool():
                with self.get_session() as session:
                    edit_ts = message.edited_timestamp
                    if not edit_ts:
                        edit_ts = None
                    else:
                        edit_ts = str(edit_ts)

                    msg = Messages(
                        message.server.id,
                        message.channel.id,
                        message.id,
                        message.content,
                        json.dumps(self.get_message_author(message)),
                        str(message.timestamp),
                        edit_ts,
                        json.dumps(self.get_message_mentions(message.mentions)),
                        json.dumps(message.attachments)
                    )
                    session.add(msg)
                    session.commit()

    def get_message_author(self, message):
        author = message.author
        obj = {
            "username": author.name,
            "discriminator": author.discriminator,
            "bot": author.bot,
            "id": author.id,
            "avatar": author.avatar
        }
        return obj

    def get_message_mentions(self, mentions):
        ments = []
        for author in mentions:
            ments.append({
                "username": author.name,
                "discriminator": author.discriminator,
                "bot": author.bot,
                "id": author.id,
                "avatar": author.avatar
            })
        return ments

    async def update_message(self, message):
        if message.server:
            async with threadpool():
                with self.get_session() as session:
                    msg = session.query(Messages) \
                        .filter(Messages.guild_id == message.server.id) \
                        .filter(Messages.channel_id == message.channel.id) \
                        .filter(Messages.message_id == message.id).first()
                    if msg:
                        msg.content = message.content
                        msg.edited_timestamp = message.edited_timestamp
                        msg.mentions = json.dumps(self.get_message_mentions(message.mentions))
                        msg.attachments = json.dumps(message.attachments)
                        msg.author = json.dumps(self.get_message_author(message))
                        session.commit()

    async def delete_message(self, message):
        if message.server:
            async with threadpool():
                with self.get_session() as session:
                    msg = session.query(Messages) \
                        .filter(Messages.guild_id == message.server.id) \
                        .filter(Messages.channel_id == message.channel.id) \
                        .filter(Messages.message_id == message.id).first()
                    if msg:
                        session.delete(msg)
                        session.commit()

    async def update_guild(self, guild):
        server_webhooks = await self.bot.get_server_webhooks(guild)
        async with threadpool():
            with self.get_session() as session:
                gui = session.query(Guilds).filter(Guilds.guild_id == guild.id).first()
                if not gui:
                    gui = Guilds(
                        guild.id,
                        guild.name,
                        json.dumps(self.get_roles_list(guild.roles)),
                        json.dumps(self.get_channels_list(guild.channels)),
                        json.dumps(self.get_webhooks_list(server_webhooks)),
                        json.dumps(self.get_emojis_list(guild.emojis)),
                        guild.owner_id,
                        guild.icon
                    )
                    session.add(gui)
                else:
                    gui.name = guild.name
                    gui.roles = json.dumps(self.get_roles_list(guild.roles))
                    gui.channels = json.dumps(self.get_channels_list(guild.channels))
                    gui.webhooks = json.dumps(self.get_webhooks_list(server_webhooks))
                    gui.emojis = json.dumps(self.get_emojis_list(guild.emojis))
                    gui.owner_id = guild.owner_id
                    gui.icon = guild.icon
                session.commit()
    
    def get_webhooks_list(self, guild_webhooks):
        webhooks = []
        for webhook in guild_webhooks:
            webhooks.append({
                "id": webhook.id,
                "guild_id": webhook.server.id,
                "channel_id": webhook.channel.id,
                "name": webhook.name,
                "token": webhook.token,
            })
        return webhooks
    
    def get_emojis_list(self, guildemojis):
        emojis = []
        for emote in guildemojis:
            emojis.append({
                "id": emote.id,
                "name": emote.name,
                "require_colons": emote.require_colons,
                "managed": emote.managed,
                "roles": self.list_role_ids(emote.roles),
                "url": emote.url
            })
        return emojis

    def get_roles_list(self, guildroles):
        roles = []
        for role in guildroles:
            roles.append({
                "id": role.id,
                "name": role.name,
                "color": role.color.value,
                "hoist": role.hoist,
                "position": role.position,
                "permissions": role.permissions.value
            })
        return roles

    def get_channels_list(self, guildchannels):
        channels = []
        for channel in guildchannels:
            if str(channel.type) == "text":
                overwrites = []
                for target, overwrite in channel.overwrites:
                    if isinstance(target, discord.Role):
                        type = "role"
                    else:
                        type = "member"
                    allow, deny = overwrite.pair()
                    allow = allow.value
                    deny = deny.value
                    overwrites.append({
                        "id": target.id,
                        "type": type,
                        "allow": allow,
                        "deny": deny,
                    })

                channels.append({
                    "id": channel.id,
                    "name": channel.name,
                    "topic": channel.topic,
                    "position": channel.position,
                    "type": str(channel.type),
                    "permission_overwrites": overwrites
                })
        return channels

    async def remove_unused_guilds(self, guilds):
        async with threadpool():
            with self.get_session() as session:
                dbguilds = session.query(Guilds).all()
                changed = False
                for guild in dbguilds:
                    disguild = discord.utils.get(guilds, id=guild.guild_id)
                    if not disguild:
                        changed = True
                        dbmsgs = session.query(Messages).filter(Messages.guild_id == guild.guild_id).all()
                        for msg in dbmsgs:
                            session.delete(msg)
                        session.delete(guild)
                if changed:
                    session.commit()

    async def remove_guild(self, guild):
        async with threadpool():
            with self.get_session() as session:
                gui = session.query(Guilds).filter(Guilds.guild_id == guild.id).first()
                if gui:
                    dbmsgs = session.query(Messages).filter(Messages.guild_id == guild.id).all()
                    for msg in dbmsgs:
                        session.delete(msg)
                    session.delete(gui)
                    session.commit()

    async def update_guild_member(self, member, active=True, banned=False):
        async with threadpool():
            with self.get_session() as session:
                dbmember = session.query(GuildMembers) \
                    .filter(GuildMembers.guild_id == member.server.id) \
                    .filter(GuildMembers.user_id == member.id).first()
                if not dbmember:
                    dbmember = GuildMembers(
                        member.server.id,
                        member.id,
                        member.name,
                        member.discriminator,
                        member.nick,
                        member.avatar,
                        active,
                        banned,
                        json.dumps(self.list_role_ids(member.roles))
                    )
                    session.add(dbmember)
                else:
                    dbmember.banned = banned
                    dbmember.active = active
                    dbmember.username = member.name
                    dbmember.discriminator = member.discriminator
                    dbmember.nickname = member.nick
                    dbmember.avatar = member.avatar
                    dbmember.roles = json.dumps(self.list_role_ids(member.roles))
                session.commit()

    async def unban_server_user(self, user, server):
        async with threadpool():
            with self.get_session() as session:
                dbmember = session.query(GuildMembers) \
                    .filter(GuildMembers.guild_id == server.id) \
                    .filter(GuildMembers.user_id == user.id).first()
                if dbmember:
                    dbmember.banned = False
                    session.commit()

    async def flag_unactive_guild_members(self, guild_id, guild_members):
        async with threadpool():
            with self.get_session() as session:
                changed = False
                dbmembers = session.query(GuildMembers) \
                    .filter(GuildMembers.guild_id == guild_id) \
                    .filter(GuildMembers.active == True).all()
                for member in dbmembers:
                    dismember = discord.utils.get(guild_members, id=member.user_id)
                    if not dismember:
                        changed = True
                        member.active = False
                if changed:
                    session.commit()

    def list_role_ids(self, usr_roles):
        ids = []
        for role in usr_roles:
            ids.append(role.id)
        return ids

    async def flag_unactive_bans(self, guild_id, guildbans):
        async with threadpool():
            with self.get_session() as session:
                changed = False
                for usr in guildbans:
                    dbusr = session.query(GuildMembers) \
                        .filter(GuildMembers.guild_id == guild_id) \
                        .filter(GuildMembers.user_id == usr.id) \
                        .filter(GuildMembers.active == False).first()
                    changed = True
                    if dbusr:
                        dbusr.banned = True
                    else:
                        dbusr = GuildMembers(
                            guild_id,
                            usr.id,
                            usr.name,
                            usr.discriminator,
                            None,
                            usr.avatar,
                            False,
                            True,
                            "[]"
                        )
                        session.add(dbusr)
                if changed:
                    session.commit()

    async def ban_unauth_user_by_query(self, guild_id, placer_id, username, discriminator):
        async with threadpool():
            with self.get_session() as session:
                dbuser = None
                if discriminator:
                    dbuser = session.query(UnauthenticatedUsers) \
                        .filter(UnauthenticatedUsers.guild_id == guild_id) \
                        .filter(UnauthenticatedUsers.username.ilike("%" + username + "%")) \
                        .filter(UnauthenticatedUsers.discriminator == discriminator) \
                        .order_by(UnauthenticatedUsers.id.desc()).first()
                else:
                    dbuser = session.query(UnauthenticatedUsers) \
                        .filter(UnauthenticatedUsers.guild_id == guild_id) \
                        .filter(UnauthenticatedUsers.username.ilike("%" + username + "%")) \
                        .order_by(UnauthenticatedUsers.id.desc()).first()
                if not dbuser:
                    return "Ban error! Guest user cannot be found."
                dbban = session.query(UnauthenticatedBans) \
                    .filter(UnauthenticatedBans.guild_id == guild_id) \
                    .filter(UnauthenticatedBans.last_username == dbuser.username) \
                    .filter(UnauthenticatedBans.last_discriminator == dbuser.discriminator).first()
                if dbban is not None:
                    if dbban.lifter_id is None:
                        return "Ban error! Guest user, **{}#{}**, has already been banned.".format(dbban.last_username, dbban.last_discriminator)
                    session.delete(dbban)
                dbban = UnauthenticatedBans(guild_id, dbuser.ip_address, dbuser.username, dbuser.discriminator, "", placer_id)
                session.add(dbban)
                session.commit()
                return "Guest user, **{}#{}**, has successfully been added to the ban list!".format(dbban.last_username, dbban.last_discriminator)

    async def revoke_unauth_user_by_query(self, guild_id, username, discriminator):
        async with threadpool():
            with self.get_session() as session:
                dbuser = None
                if discriminator:
                    dbuser = session.query(UnauthenticatedUsers) \
                        .filter(UnauthenticatedUsers.guild_id == guild_id) \
                        .filter(UnauthenticatedUsers.username.ilike("%" + username + "%")) \
                        .filter(UnauthenticatedUsers.discriminator == discriminator) \
                        .order_by(UnauthenticatedUsers.id.desc()).first()
                else:
                    dbuser = session.query(UnauthenticatedUsers) \
                        .filter(UnauthenticatedUsers.guild_id == guild_id) \
                        .filter(UnauthenticatedUsers.username.ilike("%" + username + "%")) \
                        .order_by(UnauthenticatedUsers.id.desc()).first()
                if not dbuser:
                    return "Kick error! Guest user cannot be found."
                elif dbuser.revoked:
                    return "Kick error! Guest user **{}#{}** has already been kicked!".format(dbuser.username, dbuser.discriminator)
                dbuser.revoked = True
                session.commit()
                return "Successfully kicked **{}#{}**!".format(dbuser.username, dbuser.discriminator)
                
    async def send_webserver_heartbeat(self):
        async with threadpool():
            with self.get_session() as session:
                key = "bot_heartbeat"
                q = session.query(KeyValueProperties).filter(KeyValueProperties.key == key)
                if q.count() == 0:
                    session.add(KeyValueProperties(key=key, value=time.time()))
                else:
                    firstobj = q.first()
                    firstobj.value = time.time()
                session.commit()
