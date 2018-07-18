from gino import Gino
import json
import discord
import datetime

db = Gino()

from titanembeds.database.guilds import Guilds
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
            await gui.delete()
                
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