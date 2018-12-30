import socketio
from titanembeds.utils import get_message_author, get_message_mentions, get_roles_list, get_attachments_list, get_embeds_list, get_formatted_message, get_formatted_user, get_formatted_emojis, get_formatted_guild, get_formatted_channel, get_formatted_role
import discord

class SocketIOInterface:
    def __init__(self, bot, redis_uri):
        self.io = socketio.AsyncRedisManager(redis_uri, write_only=True, channel='flask-socketio')
        self.bot = bot
    
    async def on_message(self, message):
        if message.guild:
            msg = get_formatted_message(message)
            await self.io.emit('MESSAGE_CREATE', data=msg, room=str("CHANNEL_"+str(message.channel.id)), namespace='/gateway')
    
    async def on_message_delete(self, message):
        if message.guild:
            msg = get_formatted_message(message)
            await self.io.emit('MESSAGE_DELETE', data=msg, room=str("CHANNEL_"+str(message.channel.id)), namespace='/gateway')
    
    async def on_message_update(self, message):
        if message.guild:
            msg = get_formatted_message(message)
            await self.io.emit('MESSAGE_UPDATE', data=msg, room=str("CHANNEL_"+str(message.channel.id)), namespace='/gateway')

    async def on_reaction_add(self, message):
        if message.guild:
            msg = get_formatted_message(message)
            await self.io.emit('MESSAGE_REACTION_ADD', data=msg, room=str("CHANNEL_"+str(message.channel.id)), namespace='/gateway')

    async def on_reaction_remove(self, message):
        if message.guild:
            msg = get_formatted_message(message)
            await self.io.emit('MESSAGE_REACTION_REMOVE', data=msg, room=str("CHANNEL_"+str(message.channel.id)), namespace='/gateway')

    async def on_reaction_clear(self, message):
        if message.guild:
            msg = get_formatted_message(message)
            await self.io.emit('MESSAGE_REACTION_REMOVE_ALL', data=msg, room=str("CHANNEL_"+str(message.channel.id)), namespace='/gateway')

    async def on_guild_member_add(self, member):
        user = get_formatted_user(member)
        await self.io.emit('GUILD_MEMBER_ADD', data=user, room=str("GUILD_"+str(member.guild.id)), namespace='/gateway')
        
    async def on_guild_member_remove(self, member):
        user = get_formatted_user(member)
        await self.io.emit('GUILD_MEMBER_REMOVE', data=user, room=str("GUILD_"+str(member.guild.id)), namespace='/gateway')
        
    async def on_guild_member_update(self, member):
        user = get_formatted_user(member)
        await self.io.emit('GUILD_MEMBER_UPDATE', data=user, room=str("GUILD_"+str(member.guild.id)), namespace='/gateway')
    
    async def on_guild_emojis_update(self, emojis):
        if len(emojis) == 0:
            return
        emotes = get_formatted_emojis(emojis)
        await self.io.emit('GUILD_EMOJIS_UPDATE', data=emotes, room=str("GUILD_"+str(emojis[0].guild.id)), namespace='/gateway')
    
    async def on_guild_update(self, guild):
        guildobj = get_formatted_guild(guild)
        await self.io.emit('GUILD_UPDATE', data=guildobj, room=str("GUILD_"+str(guild.id)), namespace='/gateway')
    
    async def on_channel_delete(self, channel):
        if str(channel.type) != "text":
            return
        chan = get_formatted_channel(channel)
        await self.io.emit('CHANNEL_DELETE', data=chan, room=str("GUILD_"+str(channel.guild.id)), namespace='/gateway')
    
    async def on_channel_create(self, channel):
        if str(channel.type) != "text":
            return
        chan = get_formatted_channel(channel)
        await self.io.emit('CHANNEL_CREATE', data=chan, room=str("GUILD_"+str(channel.guild.id)), namespace='/gateway')
    
    async def on_channel_update(self, channel):
        if not isinstance(channel, discord.channel.TextChannel) and not isinstance(channel, discord.channel.CategoryChannel):
            return
        chan = get_formatted_channel(channel)
        await self.io.emit('CHANNEL_UPDATE', data=chan, room=str("GUILD_"+str(channel.guild.id)), namespace='/gateway')
    
    async def on_guild_role_create(self, role):
        rol = get_formatted_role(role)
        await self.io.emit('GUILD_ROLE_CREATE', data=rol, room=str("GUILD_"+str(role.guild.id)), namespace='/gateway')

    async def on_guild_role_update(self, role):
        rol = get_formatted_role(role)
        await self.io.emit('GUILD_ROLE_UPDATE', data=rol, room=str("GUILD_"+str(role.guild.id)), namespace='/gateway')
    
    async def on_guild_role_delete(self, role):
        rol = get_formatted_role(role)
        await self.io.emit('GUILD_ROLE_DELETE', data=rol, room=str("GUILD_"+str(role.guild.id)), namespace='/gateway')