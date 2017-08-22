import socketio
from titanembeds.utils import get_message_author, get_message_mentions, get_roles_list
import time
from email import utils as emailutils

class SocketIOInterface:
    def __init__(self, bot, redis_uri):
        self.io = socketio.AsyncRedisManager(redis_uri, write_only=True, channel='flask-socketio')
        self.bot = bot
    
    def format_datetime(self, datetimeobj):
        return emailutils.formatdate(time.mktime(datetimeobj.timetuple())) # https://stackoverflow.com/questions/3453177/convert-python-datetime-to-rfc-2822
    
    def get_formatted_message(self, message):
        edit_ts = message.edited_timestamp
        if not edit_ts:
            edit_ts = None
        else:
            edit_ts = self.format_datetime(edit_ts)
        msg = {
            "id": message.id,
            "channel_id": message.channel.id,
            "content": message.content,
            "author": get_message_author(message),
            "timestamp": self.format_datetime(message.timestamp),
            "edited_timestamp": edit_ts,
            "mentions": get_message_mentions(message.mentions),
            "attachments": message.attachments,
        }
        nickname = None
        if hasattr(message.author, 'nick') and message.author.nick:
            nickname = message.author.nick
        msg["author"]["nickname"] = nickname
        for mention in msg["mentions"]:
            mention["nickname"] = None
            member = message.server.get_member(mention["id"])
            if member:
                mention["nickname"] = member.nick
        return msg
    
    async def on_message(self, message):
        if message.server:
            msg = self.get_formatted_message(message)
            await self.io.emit('MESSAGE_CREATE', data=msg, room=str("CHANNEL_"+message.channel.id), namespace='/gateway')
    
    async def on_message_delete(self, message):
        if message.server:
            msg = self.get_formatted_message(message)
            await self.io.emit('MESSAGE_DELETE', data=msg, room=str("CHANNEL_"+message.channel.id), namespace='/gateway')
    
    async def on_message_update(self, message):
        if message.server:
            msg = self.get_formatted_message(message)
            await self.io.emit('MESSAGE_UPDATE', data=msg, room=str("CHANNEL_"+message.channel.id), namespace='/gateway')
    
    def get_formatted_user(self, user):
        userobj = {
            "avatar": user.avatar,
            "avatar_url": user.avatar_url,
            "color": str(user.color)[1:],
            "discriminator": user.discriminator,
            "game": None,
            "hoist-role": None,
            "id": user.id,
            "status": str(user.status),
            "username": user.name,
            "nick": None,
        }
        if user.nick:
            userobj["nick"] = user.nick
        if user.game:
            userobj["game"] = {
                "name": user.game.name
            }
        roles = sorted(user.roles, key=lambda k: k.position, reverse=True)
        for role in roles:
            if role.hoist:
                userobj["hoist-role"] = {
                    "id": role.id,
                    "name": role.name,
                    "position": role.position,
                }
                break
        return userobj

    async def on_guild_member_add(self, member):
        user = self.get_formatted_user(member)
        await self.io.emit('GUILD_MEMBER_ADD', data=user, room=str("GUILD_"+member.server.id), namespace='/gateway')
        
    async def on_guild_member_remove(self, member):
        user = self.get_formatted_user(member)
        await self.io.emit('GUILD_MEMBER_REMOVE', data=user, room=str("GUILD_"+member.server.id), namespace='/gateway')
        
    async def on_guild_member_update(self, member):
        user = self.get_formatted_user(member)
        await self.io.emit('GUILD_MEMBER_UPDATE', data=user, room=str("GUILD_"+member.server.id), namespace='/gateway')
    
    def get_formatted_emojis(self, emojis):
        emotes = []
        for emo in emojis:
            emotes.append({
                "id": emo.id,
                "managed": emo.managed,
                "name": emo.name,
                "require_colons": emo.require_colons,
                "roles": get_roles_list(emo.roles),
                "url": emo.url,
            })
        return emotes
    
    async def on_guild_emojis_update(self, emojis):
        emotes = self.get_formatted_emojis(emojis)
        await self.io.emit('GUILD_EMOJIS_UPDATE', data=emotes, room=str("GUILD_"+emojis[0].server.id), namespace='/gateway')