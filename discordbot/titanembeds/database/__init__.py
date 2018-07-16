from gino import Gino
import json
import discord
import datetime

db = Gino()

from titanembeds.database.guilds import Guilds
from titanembeds.database.guild_members import GuildMembers
from titanembeds.database.unauthenticated_users import UnauthenticatedUsers
from titanembeds.database.unauthenticated_bans import UnauthenticatedBans

from titanembeds.utils import get_message_author, get_message_mentions, get_webhooks_list, get_emojis_list, get_roles_list, get_channels_list, list_role_ids, get_attachments_list, get_embeds_list

class DatabaseInterface(object):
    def __init__(self, bot):
        self.bot = bot

    async def connect(self, dburi):
        await db.set_bind(dburi)
    
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
                discriminator = int(member.discriminator),
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
                    discriminator = int(member.discriminator),
                    nickname = member.nick,
                    avatar = member.avatar,
                    roles = json.dumps(list_role_ids(member.roles))
                ).apply()
    
    async def unban_server_user(self, user, server):
        await GuildMembers.update.values(banned = False) \
            .where(GuildMembers.guild_id == int(server.id)) \
            .where(GuildMembers.user_id == int(user.id)) \
            .gino.status()


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
                    discriminator = int(usr.discriminator),
                    nickname = None,
                    avatar = usr.avatar,
                    active = False,
                    banned = True,
                    roles = "[]"
                )
                
    async def ban_unauth_user_by_query(self, guild_id, placer_id, username, discriminator):
        dbuser = None
        if discriminator:
            dbuser = await UnauthenticatedUsers.query \
                .where(UnauthenticatedUsers.guild_id == int(guild_id)) \
                .where(UnauthenticatedUsers.username.ilike("%" + username + "%")) \
                .where(UnauthenticatedUsers.discriminator == discriminator) \
                .order_by(UnauthenticatedUsers.id.desc()).gino.first()
        else:
            dbuser = await UnauthenticatedUsers.query \
                .where(UnauthenticatedUsers.guild_id == int(guild_id)) \
                .where(UnauthenticatedUsers.username.ilike("%" + username + "%")) \
                .order_by(UnauthenticatedUsers.id.desc()).gino.first()
        if not dbuser:
            return "Ban error! Guest user cannot be found."
        dbban = await UnauthenticatedBans.query \
            .where(UnauthenticatedBans.guild_id == int(guild_id)) \
            .where(UnauthenticatedBans.last_username == dbuser.username) \
            .where(UnauthenticatedBans.last_discriminator == dbuser.discriminator).gino.first()
        if dbban is not None:
            if dbban.lifter_id is None:
                return "Ban error! Guest user, **{}#{}**, has already been banned.".format(dbban.last_username, dbban.last_discriminator)
            await dbban.delete()
        dbban = await UnauthenticatedBans.create(
            guild_id = int(guild_id),
            ip_address = dbuser.ip_address,
            last_username = dbuser.username,
            last_discriminator = dbuser.discriminator,
            timestamp = datetime.datetime.now(),
            reason = "",
            lifter_id = None,
            placer_id = int(placer_id)
        )
        return "Guest user, **{}#{}**, has successfully been added to the ban list!".format(dbban.last_username, dbban.last_discriminator)

    async def revoke_unauth_user_by_query(self, guild_id, username, discriminator):
        dbuser = None
        if discriminator:
            dbuser = await UnauthenticatedUsers.query \
                .where(UnauthenticatedUsers.guild_id == int(guild_id)) \
                .where(UnauthenticatedUsers.username.ilike("%" + username + "%")) \
                .where(UnauthenticatedUsers.discriminator == discriminator) \
                .order_by(UnauthenticatedUsers.id.desc()).gino.first()
        else:
            dbuser = await UnauthenticatedUsers.query \
                .where(UnauthenticatedUsers.guild_id == int(guild_id)) \
                .where(UnauthenticatedUsers.username.ilike("%" + username + "%")) \
                .order_by(UnauthenticatedUsers.id.desc()).gino.first()
        if not dbuser:
            return "Kick error! Guest user cannot be found."
        elif dbuser.revoked:
            return "Kick error! Guest user **{}#{}** has already been kicked!".format(dbuser.username, dbuser.discriminator)
        await dbuser.update(revoked = True).apply()
        return "Successfully kicked **{}#{}**!".format(dbuser.username, dbuser.discriminator)

    async def delete_all_messages_from_channel(self, channel_id):
        await Messages.delete.where(Messages.channel_id == int(channel_id)).gino.status()