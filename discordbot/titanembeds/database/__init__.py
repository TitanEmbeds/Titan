from contextlib import contextmanager
from asyncio_extras import threadpool
import sqlalchemy as db
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

import json
import discord

Base = declarative_base()

from titanembeds.database.guilds import Guilds
from titanembeds.database.messages import Messages
from titanembeds.database.guild_members import GuildMembers
from titanembeds.database.unauthenticated_users import UnauthenticatedUsers
from titanembeds.database.unauthenticated_bans import UnauthenticatedBans

from titanembeds.utils import get_message_author, get_message_mentions, get_webhooks_list, get_emojis_list, get_roles_list, get_channels_list, list_role_ids, get_attachments_list, get_embeds_list

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
        got_session = False
        while not got_session:
            try:
                session = self._sessionmaker()  # type: Session
                got_session = True
            except:
                pass
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    async def push_message(self, message):
        if message.guild:
            async with threadpool():
                with self.get_session() as session:
                    edit_ts = message.edited_at
                    if not edit_ts:
                        edit_ts = None
                    else:
                        edit_ts = str(edit_ts)

                    msg = Messages(
                        int(message.guild.id),
                        int(message.channel.id),
                        int(message.id),
                        message.content,
                        json.dumps(get_message_author(message)),
                        str(message.created_at),
                        edit_ts,
                        json.dumps(get_message_mentions(message.mentions)),
                        json.dumps(get_attachments_list(message.attachments)),
                        json.dumps(get_embeds_list(message.embeds))
                    )
                    session.add(msg)
                    session.commit()

    async def update_message(self, message):
        if message.guild:
            async with threadpool():
                with self.get_session() as session:
                    msg = session.query(Messages) \
                        .filter(Messages.guild_id == message.guild.id) \
                        .filter(Messages.channel_id == message.channel.id) \
                        .filter(Messages.message_id == message.id).first()
                    if msg:
                        msg.content = message.content
                        msg.timestamp = message.created_at
                        msg.edited_timestamp = message.edited_at
                        msg.mentions = json.dumps(get_message_mentions(message.mentions))
                        msg.attachments = json.dumps(get_attachments_list(message.attachments))
                        msg.embeds = json.dumps(get_embeds_list(message.embeds))
                        msg.author = json.dumps(get_message_author(message))
                        session.commit()

    async def delete_message(self, message):
        if message.guild:
            async with threadpool():
                with self.get_session() as session:
                    msg = session.query(Messages) \
                        .filter(Messages.guild_id == int(message.guild.id)) \
                        .filter(Messages.channel_id == int(message.channel.id)) \
                        .filter(Messages.message_id == int(message.id)).first()
                    if msg:
                        session.delete(msg)
                        session.commit()

    async def update_guild(self, guild):
        if guild.me.guild_permissions.manage_webhooks:
            try:
                server_webhooks = await guild.webhooks()
            except:
                server_webhooks = []
        else:
            server_webhooks = []
        async with threadpool():
            with self.get_session() as session:
                gui = session.query(Guilds).filter(Guilds.guild_id == guild.id).first()
                if not gui:
                    gui = Guilds(
                        int(guild.id),
                        guild.name,
                        json.dumps(get_roles_list(guild.roles)),
                        json.dumps(get_channels_list(guild.channels)),
                        json.dumps(get_webhooks_list(server_webhooks)),
                        json.dumps(get_emojis_list(guild.emojis)),
                        int(guild.owner_id),
                        guild.icon
                    )
                    session.add(gui)
                else:
                    gui.name = guild.name
                    gui.roles = json.dumps(get_roles_list(guild.roles))
                    gui.channels = json.dumps(get_channels_list(guild.channels))
                    gui.webhooks = json.dumps(get_webhooks_list(server_webhooks))
                    gui.emojis = json.dumps(get_emojis_list(guild.emojis))
                    gui.owner_id = int(guild.owner_id)
                    gui.icon = guild.icon
                session.commit()

    async def remove_unused_guilds(self, guilds):
        async with threadpool():
            with self.get_session() as session:
                dbguilds = session.query(Guilds).all()
                changed = False
                for guild in dbguilds:
                    disguild = discord.utils.get(guilds, id=guild.guild_id)
                    if not disguild:
                        changed = True
                        dbmsgs = session.query(Messages).filter(Messages.guild_id == int(guild.guild_id)).all()
                        for msg in dbmsgs:
                            session.delete(msg)
                        session.delete(guild)
                if changed:
                    session.commit()

    async def remove_guild(self, guild):
        async with threadpool():
            with self.get_session() as session:
                gui = session.query(Guilds).filter(Guilds.guild_id == int(guild.id)).first()
                if gui:
                    dbmsgs = session.query(Messages).filter(Messages.guild_id == int(guild.id)).delete()
                    session.delete(gui)
                    session.commit()

    async def update_guild_member(self, member, active=True, banned=False, guild=None):
        async with threadpool():
            with self.get_session() as session:
                if guild:
                    dbmember = session.query(GuildMembers) \
                        .filter(GuildMembers.guild_id == int(guild.id)) \
                        .filter(GuildMembers.user_id == int(member.id)) \
                        .order_by(GuildMembers.id).all()
                else:
                    dbmember = session.query(GuildMembers) \
                        .filter(GuildMembers.guild_id == int(member.guild.id)) \
                        .filter(GuildMembers.user_id == int(member.id)) \
                        .order_by(GuildMembers.id).all()
                if not dbmember:
                    dbmember = GuildMembers(
                        int(member.guild.id),
                        int(member.id),
                        member.name,
                        member.discriminator,
                        member.nick,
                        member.avatar,
                        active,
                        banned,
                        json.dumps(list_role_ids(member.roles))
                    )
                    session.add(dbmember)
                else:
                    if len(dbmember) > 1:
                        for mem in dbmember[1:]:
                            session.delete(mem)
                    dbmember = dbmember[0]
                    if dbmember.banned != banned or dbmember.active != active or dbmember.username != member.name or dbmember.discriminator != int(member.discriminator) or dbmember.nickname != member.nick or dbmember.avatar != member.avatar or set(json.loads(dbmember.roles)) != set(list_role_ids(member.roles)):
                        dbmember.banned = banned
                        dbmember.active = active
                        dbmember.username = member.name
                        dbmember.discriminator = member.discriminator
                        dbmember.nickname = member.nick
                        dbmember.avatar = member.avatar
                        dbmember.roles = json.dumps(list_role_ids(member.roles))
                session.commit()

    async def unban_server_user(self, user, server):
        async with threadpool():
            with self.get_session() as session:
                dbmember = session.query(GuildMembers) \
                    .filter(GuildMembers.guild_id == int(server.id)) \
                    .filter(GuildMembers.user_id == int(user.id)).first()
                if dbmember:
                    dbmember.banned = False
                    session.commit()

    async def flag_unactive_guild_members(self, guild_id, guild_members):
        async with threadpool():
            with self.get_session() as session:
                changed = False
                dbmembers = session.query(GuildMembers) \
                    .filter(GuildMembers.guild_id == int(guild_id)) \
                    .filter(GuildMembers.active == True).all()
                for member in dbmembers:
                    dismember = discord.utils.get(guild_members, id=member.user_id)
                    if not dismember:
                        changed = True
                        member.active = False
                if changed:
                    session.commit()

    async def flag_unactive_bans(self, guild_id, guildbans):
        async with threadpool():
            with self.get_session() as session:
                changed = False
                for usr in guildbans:
                    dbusr = session.query(GuildMembers) \
                        .filter(GuildMembers.guild_id == int(guild_id)) \
                        .filter(GuildMembers.user_id == int(usr.id)) \
                        .filter(GuildMembers.active == False).first()
                    changed = True
                    if dbusr:
                        dbusr.banned = True
                    else:
                        dbusr = GuildMembers(
                            int(guild_id),
                            int(usr.id),
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
                        .filter(UnauthenticatedUsers.guild_id == int(guild_id)) \
                        .filter(UnauthenticatedUsers.username.ilike("%" + username + "%")) \
                        .filter(UnauthenticatedUsers.discriminator == discriminator) \
                        .order_by(UnauthenticatedUsers.id.desc()).first()
                else:
                    dbuser = session.query(UnauthenticatedUsers) \
                        .filter(UnauthenticatedUsers.guild_id == int(guild_id)) \
                        .filter(UnauthenticatedUsers.username.ilike("%" + username + "%")) \
                        .order_by(UnauthenticatedUsers.id.desc()).first()
                if not dbuser:
                    return "Ban error! Guest user cannot be found."
                dbban = session.query(UnauthenticatedBans) \
                    .filter(UnauthenticatedBans.guild_id == int(guild_id)) \
                    .filter(UnauthenticatedBans.last_username == dbuser.username) \
                    .filter(UnauthenticatedBans.last_discriminator == dbuser.discriminator).first()
                if dbban is not None:
                    if dbban.lifter_id is None:
                        return "Ban error! Guest user, **{}#{}**, has already been banned.".format(dbban.last_username, dbban.last_discriminator)
                    session.delete(dbban)
                dbban = UnauthenticatedBans(int(guild_id), dbuser.ip_address, dbuser.username, dbuser.discriminator, "", int(placer_id))
                session.add(dbban)
                session.commit()
                return "Guest user, **{}#{}**, has successfully been added to the ban list!".format(dbban.last_username, dbban.last_discriminator)

    async def revoke_unauth_user_by_query(self, guild_id, username, discriminator):
        async with threadpool():
            with self.get_session() as session:
                dbuser = None
                if discriminator:
                    dbuser = session.query(UnauthenticatedUsers) \
                        .filter(UnauthenticatedUsers.guild_id == int(guild_id)) \
                        .filter(UnauthenticatedUsers.username.ilike("%" + username + "%")) \
                        .filter(UnauthenticatedUsers.discriminator == discriminator) \
                        .order_by(UnauthenticatedUsers.id.desc()).first()
                else:
                    dbuser = session.query(UnauthenticatedUsers) \
                        .filter(UnauthenticatedUsers.guild_id == int(guild_id)) \
                        .filter(UnauthenticatedUsers.username.ilike("%" + username + "%")) \
                        .order_by(UnauthenticatedUsers.id.desc()).first()
                if not dbuser:
                    return "Kick error! Guest user cannot be found."
                elif dbuser.revoked:
                    return "Kick error! Guest user **{}#{}** has already been kicked!".format(dbuser.username, dbuser.discriminator)
                dbuser.revoked = True
                session.commit()
                return "Successfully kicked **{}#{}**!".format(dbuser.username, dbuser.discriminator)
                
    async def delete_all_messages_from_channel(self, channel_id):
        async with threadpool():
            with self.get_session() as session:
                session.query(Messages).filter(Messages.channel_id == int(channel_id)).delete()
                session.commit()