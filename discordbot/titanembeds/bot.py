from config import config
from titanembeds.database import DatabaseInterface
from titanembeds.commands import Commands
from titanembeds.socketio import SocketIOInterface
from titanembeds.poststats import DiscordBotsOrg, BotsDiscordPw
from collections import deque
import discord
import aiohttp
import asyncio
import sys
import logging
import json
import zlib
logging.basicConfig(filename='titanbot.log',level=logging.INFO,format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
handler = logging.FileHandler(config.get("logging-location", "titanbot.log"))
logging.getLogger('TitanBot')
logging.getLogger('sqlalchemy')

class Titan(discord.AutoShardedClient):
    def __init__(self):
        game = discord.Game(name="Embed your Discord server! Visit https://TitanEmbeds.com/")
        super().__init__(max_messages=20000, game=game)
        self.aiosession = aiohttp.ClientSession(loop=self.loop)
        self.http.user_agent += ' TitanEmbeds-Bot'
        self.database = DatabaseInterface(self)
        self.command = Commands(self, self.database)
        self.socketio = SocketIOInterface(self, config["redis-uri"])
        
        self.delete_list = deque(maxlen=100) # List of msg ids to prevent duplicate delete
        self.zlib_obj = zlib.decompressobj()
        self.buffer_arr = bytearray()
        
        self.discordBotsOrg = None
        self.botsDiscordPw = None

    def _cleanup(self):
        try:
            self.loop.run_until_complete(self.logout())
        except: # Can be ignored
            pass
        pending = asyncio.Task.all_tasks()
        gathered = asyncio.gather(*pending)
        try:
            gathered.cancel()
            self.loop.run_until_complete(gathered)
            gathered.exception()
        except: # Can be ignored
            pass

    def run(self):
        try:
            self.loop.run_until_complete(self.start(config["bot-token"]))
        except discord.errors.LoginFailure:
            print("Invalid bot token in config!")
        finally:
            try:
                self._cleanup()
            except Exception as e:
                print("Error in cleanup:", e)
            self.loop.close()

    async def on_ready(self):
        print('Titan [DiscordBot]')
        print('Logged in as the following user:')
        print(self.user.name)
        print(self.user.id)
        print('------')
        print("Shard count: " + str(self.shard_count))
        print("------")

        try:
            await self.database.connect(config["database-uri"])
        except Exception:
            self.logger.error("Unable to connect to specified database!")
            traceback.print_exc()
            await self.logout()
            return
        
        self.discordBotsOrg = DiscordBotsOrg(self.user.id, config.get("discord-bots-org-token", None))
        self.botsDiscordPw = BotsDiscordPw(self.user.id, config.get("bots-discord-pw-token", None))
        await self.postStats()

    async def on_message(self, message):
        await self.socketio.on_message(message)
        await self.database.push_message(message)

        msg_arr = message.content.split() # split the message
        if len(message.content.split()) > 1 and message.guild: #making sure there is actually stuff in the message and have arguments and check if it is sent in server (not PM)
            if msg_arr[0] == "<@{}>".format(self.user.id) or msg_arr[0] == "<@!{}>".format(self.user.id): #make sure it is mention
                msg_cmd = msg_arr[1].lower() # get command
                cmd = getattr(self.command, msg_cmd, None) #check if cmd exist, if not its none
                if cmd: # if cmd is not none...
                    await self.send_typing(message.channel) #this looks nice
                    await getattr(self.command, msg_cmd)(message) #actually run cmd, passing in msg obj

    async def on_message_edit(self, message_before, message_after):
        await self.database.update_message(message_after)
        await self.socketio.on_message_update(message_after)

    async def on_message_delete(self, message):
        self.delete_list.append(message.id)
        await self.database.delete_message(message)
        await self.socketio.on_message_delete(message)

    async def on_guild_join(self, guild):
        await self.database.update_guild(guild)
        for member in guild.members:
            await self.database.update_guild_member(member, True, False)
        if guild.me.guild_permissions.ban_members:
            banned = await guild.bans()
            for ban in banned:
                member = discord.Member(user={
                    "username": ban.name,
                    "id": ban.id,
                    "discriminator": ban.discriminator,
                    "avatar": ban.avatar,
                    "bot": ban.bot
                })
                await self.database.update_guild_member(member, False, True)
        for channel in list(guild.channels):
            chanperm = channel.permissions_for(channel.guild.me)
            if not chanperm.read_messages or not chanperm.read_message_history or not isinstance(channel, discord.channel.TextChannel):
                continue
            async for message in channel.history(limit=50, reverse=True):
                try:
                    await self.database.push_message(message)
                except:
                    pass
        await self.postStats()

    async def on_guild_remove(self, guild):
        await self.database.remove_guild(guild)
        await self.postStats()

    async def on_guild_update(self, guildbefore, guildafter):
        await self.database.update_guild(guildafter)
        await self.socketio.on_guild_update(guildafter)

    async def on_guild_role_create(self, role):
        if role.name == self.user.name and role.managed:
            await asyncio.sleep(2)
        await self.database.update_guild(role.guild)
        await self.socketio.on_guild_role_create(role)

    async def on_guild_role_delete(self, role):
        if role.guild.me not in role.guild.members:
            return
        await self.database.update_guild(role.guild)
        await self.socketio.on_guild_role_delete(role)

    async def on_guild_role_update(self, rolebefore, roleafter):
        await self.database.update_guild(roleafter.guild)
        await self.socketio.on_guild_role_update(roleafter)

    async def on_channel_delete(self, channel):
        if channel.guild:
            await self.database.update_guild(channel.guild)
            await self.socketio.on_channel_delete(channel)

    async def on_channel_create(self, channel):
        if channel.guild:
            await self.database.update_guild(channel.guild)
            await self.socketio.on_channel_create(channel)

    async def on_channel_update(self, channelbefore, channelafter):
        await self.database.update_guild(channelafter.guild)
        await self.socketio.on_channel_update(channelafter)

    async def on_member_join(self, member):
        await self.database.update_guild_member(member, active=True, banned=False)
        await self.socketio.on_guild_member_add(member)

    async def on_member_remove(self, member):
        await self.database.update_guild_member(member, active=False, banned=False)
        await self.socketio.on_guild_member_remove(member)

    async def on_member_update(self, memberbefore, memberafter):
        if set(memberbefore.roles) != set(memberafter.roles) or memberbefore.avatar != memberafter.avatar or memberbefore.nick != memberafter.nick or memberbefore.name != memberafter.name or memberbefore.discriminator != memberafter.discriminator or memberbefore.status != memberafter.status:
            if memberbefore.status == memberafter.status:
                await self.database.update_guild_member(memberafter)
            await self.socketio.on_guild_member_update(memberafter)

    async def on_member_ban(self, member):
        if self.user.id == member.id:
            return
        await self.database.update_guild_member(member, active=False, banned=True)

    async def on_member_unban(self, guild, user):
        await self.database.unban_server_user(user, guild)
    
    async def on_guild_emojis_update(self, guild, before, after):
        if len(after) == 0:
            await self.database.update_guild(guild)
            await self.socketio.on_guild_emojis_update(before)
        else:
            await self.database.update_guild(guild)
            await self.socketio.on_guild_emojis_update(after)
            
    async def on_webhooks_update(self, guild, channel):
        await self.database.update_guild(guild)

    async def on_socket_raw_receive(self, msg):
        if isinstance(msg, bytes):
            self.buffer_arr.extend(msg)

            if len(msg) >= 4:
                if msg[-4:] == b'\x00\x00\xff\xff':
                    msg = self.zlib_obj.decompress(self.buffer_arr)
                    msg = msg.decode('utf-8')
                    self.buffer_arr = bytearray()
                else:
                    return
            else:
                return

        msg = json.loads(msg)
        if msg["op"] != 0:
            return
        action = msg["t"]
        if action == "MESSAGE_UPDATE":
            if not self.in_messages_cache(msg["d"]["id"]):
                channel = self.get_channel(msg["d"]["channel_id"])
                message = await self.get_message(channel, msg["d"]["id"])
                await self.on_message_edit(None, message)
        if action == "MESSAGE_DELETE":
            if not self.in_messages_cache(msg["d"]["id"]):
                await asyncio.sleep(1)
                await self.process_raw_message_delete(msg["d"]["id"], msg["d"]["channel_id"])
        if action == "MESSAGE_DELETE_BULK":
            await asyncio.sleep(1)
            for msgid in msg["d"]["ids"]:
                if not self.in_messages_cache(msgid):
                    await self.process_raw_message_delete(msgid, msg["d"]["channel_id"])
    
    async def process_raw_message_delete(self, msg_id, channel_id):
        if msg_id in self.delete_list:
            self.delete_list.remove(msg_id)
            return
        channel = self.get_channel(int(channel_id))
        data = {'content': "What fun is there in making sense?", 'type': 0, 'edited_timestamp': None, 'id': msg_id, 'channel_id': channel_id, 'timestamp': '2017-01-15T02:59:58+00:00'}
        msg = discord.Message(channel=channel, state=self._connection, data=data) # Procreate a fake message object
        await self.on_message_delete(msg)
    
    def in_messages_cache(self, msg_id):
        for msg in self._connection._messages:
            if msg.id == msg_id:
                return True
        return False
        
    async def postStats(self):
        count = len(self.guilds)
        shard_count = self.shard_count
        shard_id = self.shard_id
        await self.discordBotsOrg.post(count, shard_count, shard_id)
        await self.botsDiscordPw.post(count, shard_count, shard_id)
