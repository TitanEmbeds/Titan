from gino import Gino
import json
import discord

db = Gino()

from titanembeds.database.guilds import Guilds
from titanembeds.database.messages import Messages
from titanembeds.database.guild_members import GuildMembers
from titanembeds.database.unauthenticated_users import UnauthenticatedUsers
from titanembeds.database.unauthenticated_bans import UnauthenticatedBans

from titanembeds.utils import get_message_author, get_message_mentions, get_webhooks_list, get_emojis_list, get_roles_list, get_channels_list, list_role_ids, get_attachments_list, get_embeds_list

class DatabaseInterface(object):
    def __init__(self, bot):
        self.bot = bot

    async def connect(self, dburi):
        await db.set_bind(dburi)

    async def push_message(self, message):
        if message.guild:
            edit_ts = message.edited_at
            if not edit_ts:
                edit_ts = None
            else:
                edit_ts = str(edit_ts)
            await Messages.create(
                message_id = int(message.id),
                guild_id = int(message.guild.id),
                channel_id = int(message.channel.id),
                content = message.content,
                author = json.dumps(get_message_author(message)),
                timestamp = str(message.created_at),
                edited_timestamp = edit_ts,
                mentions = json.dumps(get_message_mentions(message.mentions)),
                attachments = json.dumps(get_attachments_list(message.attachments)),
                embeds = json.dumps(get_embeds_list(message.embeds))
            )
                
    async def update_message(self, message):
        if message.guild:
            await Messages.get(int(message.id)).update(
                content = message.content,
                timestamp = message.created_at,
                edited_timestamp = message.edited_at,
                mentions = json.dumps(get_message_mentions(message.mentions)),
                attachments = json.dumps(get_attachments_list(message.attachments)),
                embeds = json.dumps(get_embeds_list(message.embeds)),
                author = json.dumps(get_message_author(message))
            ).apply()

    async def delete_message(self, message):
        if message.guild:
            await Messages.get(int(message.id)).delete()
    
    async def update_guild(self, guild):
        if guild.me.guild_permissions.manage_webhooks:
            try:
                server_webhooks = await guild.webhooks()
            except:
                server_webhooks = []
        else:
            server_webhooks = []
        gui = await Guilds.get(guild.id)
        if not gui:
            await Guilds.create(
                guild_id = int(guild.id),
                name = guild.name,
                unauth_users = True,
                visitor_view = False,
                webhook_messages = False,
                guest_icon = None,
                chat_links = True,
                bracket_links = True,
                unauth_captcha = True,
                mentions_limit = -1,
                roles = json.dumps(get_roles_list(guild.roles)),
                channels = json.dumps(get_channels_list(guild.channels)),
                webhooks = json.dumps(get_webhooks_list(server_webhooks)),
                emojis = json.dumps(get_emojis_list(guild.emojis)),
                owner_id = int(guild.owner_id),
                icon = guild.icon
            )
        else:
            await gui.update(
                name = guild.name,
                roles = json.dumps(get_roles_list(guild.roles)),
                channels = json.dumps(get_channels_list(guild.channels)),
                webhooks = json.dumps(get_webhooks_list(server_webhooks)),
                emojis = json.dumps(get_emojis_list(guild.emojis)),
                owner_id = int(guild.owner_id),
                icon = guild.icon
            ).apply()

    async def remove_unused_guilds(self, guilds):
        dbguilds = await Guilds.query.gino.all()
        for guild in dbguilds:
            disguild = discord.utils.get(guilds, id=guild.guild_id)
            if not disguild:
                await Messages.delete.where(Messages.guild_id == int(guild.guild_id)).gino.status()

    async def remove_guild(self, guild):
        gui = await Guilds.get(int(guild.id))
        if gui:
            await Messages.delete.where(Messages.guild_id == int(guild.id)).gino.status()
            await gui.delete()
    
    async def update_guild_member(self, member, active=True, banned=False, guild=None):
        if guild:
            dbmember = await GuildMembers.query \
                .where(GuildMembers.guild_id == int(guild.id)) \
                .where(GuildMembers.user_id == int(member.id)) \
                .order_by(GuildMembers.id).gino.all()
        else:
            dbmember = await GuildMembers.query \
                .where(GuildMembers.guild_id == int(member.guild.id)) \
                .where(GuildMembers.user_id == int(member.id)) \
                .order_by(GuildMembers.id).gino.all()
        if not dbmember:
            await GuildMembers.create(
                guild_id = int(member.guild.id),
                user_id = int(member.id),
                username = member.name,
                discriminator = member.discriminator,
                nickname = member.nick,
                avatar = member.avatar,
                active = active,
                banned = banned,
                roles = json.dumps(list_role_ids(member.roles))
            )
        else:
            if len(dbmember) > 1:
                for mem in dbmember[1:]:
                    await mem.delete()
                dbmember = dbmember[0]
            if dbmember.banned != banned or dbmember.active != active or dbmember.username != member.name or dbmember.discriminator != int(member.discriminator) or dbmember.nickname != member.nick or dbmember.avatar != member.avatar or set(json.loads(dbmember.roles)) != set(list_role_ids(member.roles)):
                await dbmember.update(
                    banned = banned,
                    active = active,
                    username = member.name,
                    discriminator = member.discriminator,
                    nickname = member.nick,
                    avatar = member.avatar,
                    roles = json.dumps(list_role_ids(member.roles))
                ).apply()
    
    async def unban_server_user(self, user, server):
        await GuildMembers.query \
            .where(GuildMembers.guild_id == int(server.id)) \
            .where(GuildMembers.user_id == int(user.id)) \
            .update(banned = False).apply()

    async def flag_unactive_guild_members(self, guild_id, guild_members):
        async with db.transaction():
            async for member in GuildMembers.query \
                .where(GuildMembers.guild_id == int(guild_id)) \
                .where(GuildMembers.active == True).gino.iterate():
                dismember = discord.utils.get(guild_members, id=member.user_id)
                if not dismember:
                    await member.update(active = False).apply()

    async def flag_unactive_bans(self, guild_id, guildbans):
        for usr in guildbans:
            dbusr = await GuildMembers.query \
                .where(GuildMembers.guild_id == int(guild_id)) \
                .where(GuildMembers.user_id == int(usr.id)) \
                .where(GuildMembers.active == False).gino.first()
            if dbusr:
                dbusr.update(banned=True).apply()
            else:
                await GuildMembers.create(
                    guild_id = int(guild_id),
                    user_id = int(usr.id),
                    username = usr.name,
                    discriminator = usr.discriminator,
                    nickname = None,
                    avatar = usr.avatar,
                    active = False,
                    banned = True,
                    roles = "[]"
                )
                
    async def ban_unauth_user_by_query(self, guild_id, placer_id, username, discriminator):
        self.bot.loop.run_in_executor(None, self._ban_unauth_user_by_query, guild_id, placer_id, username, discriminator)

    def _ban_unauth_user_by_query(self, guild_id, placer_id, username, discriminator):
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
        self.bot.loop.run_in_executor(None, self._revoke_unauth_user_by_query, guild_id, username, discriminator)

    def _revoke_unauth_user_by_query(self, guild_id, username, discriminator):
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
        await Messages.delete.where(Messages.channel_id == int(channel_id)).gino.status()