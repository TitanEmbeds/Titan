from config import config
from titanembeds.redisqueue import RedisQueue
from titanembeds.commands import Commands
from titanembeds.socketio import SocketIOInterface
from titanembeds.poststats import DiscordBotsOrg, BotsDiscordPw
from collections import deque
# from raven import Client as RavenClient
# import raven
import discord
import aiohttp
import asyncio
import sys
import logging
import json
# try:
#     raven_client = RavenClient(config["sentry-dsn"])
# except raven.exceptions.InvalidDsn:
#     pass
import traceback

intents = discord.Intents.default()
intents.members = True

class Titan(discord.AutoShardedClient):
    def __init__(self, shard_ids=None, shard_count=None):
        super().__init__(
            shard_ids=shard_ids,
            shard_count=shard_count,
            max_messages=10000,
            intents=intents,
            activity=discord.Game(name="Embed your Discord server! Visit https://TitanEmbeds.com/")
        )
        self.setup_logger(shard_ids)
        self.aiosession = aiohttp.ClientSession(loop=self.loop)
        self.http.user_agent += ' TitanEmbeds-Bot'
        self.redisqueue = RedisQueue(self, config["redis-uri"])
        self.command = Commands(self, config)
        self.socketio = SocketIOInterface(self, config["redis-uri"])
        
        self.delete_list = deque(maxlen=100) # List of msg ids to prevent duplicate delete
        
        self.discordBotsOrg = None
        self.botsDiscordPw = None

    def setup_logger(self, shard_ids=None):
        shard_ids = '-'.join(str(x) for x in shard_ids) if shard_ids is not None else ''
        logging.basicConfig(
            filename='titanbot{}.log'.format(shard_ids),
            level=logging.INFO,
            format='%(asctime)s %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p'
        )
        logging.getLogger('TitanBot')

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
    
    async def start(self):
        await self.redisqueue.connect()
        await super().start(config["bot-token"])

    async def on_shard_ready(self, shard_id):
        logging.info('Titan [DiscordBot]')
        logging.info('Logged in as the following user:')
        logging.info(self.user.name)
        logging.info(self.user.id)
        logging.info('------')
        logging.info("Shard count: " + str(self.shard_count))
        logging.info("Shard id: "+ str(shard_id))
        logging.info("------")
        return
        self.loop.create_task(self.redisqueue.subscribe())
        
        self.discordBotsOrg = DiscordBotsOrg(self.user.id, config.get("discord-bots-org-token", None))
        self.botsDiscordPw = BotsDiscordPw(self.user.id, config.get("bots-discord-pw-token", None))
        self.loop.create_task(self.auto_post_stats())

    async def on_socket_raw_send(self, data):
        data = str(data)
        try:
            data = json.loads(data)
        except:
            return
        logging.info('DEBUG LOG {}'.format(data.get("op", -1)))
        logging.info('{}'.format(str(list(traceback.format_stack()))))

    async def on_message(self, message):
        return
        await self.socketio.on_message(message)
        await self.redisqueue.push_message(message)

        msg_arr = message.content.split() # split the message
        if len(message.content.split()) > 1 and message.guild: #making sure there is actually stuff in the message and have arguments and check if it is sent in server (not PM)
            if msg_arr[0] == "<@{}>".format(self.user.id) or msg_arr[0] == "<@!{}>".format(self.user.id): #make sure it is mention
                msg_cmd = msg_arr[1].lower() # get command
                if msg_cmd == "__init__":
                    return
                cmd = getattr(self.command, msg_cmd, None) #check if cmd exist, if not its none
                if cmd: # if cmd is not none...
                    async with message.channel.typing(): #this looks nice
                        await getattr(self.command, msg_cmd)(message) #actually run cmd, passing in msg obj

    async def on_message_edit(self, message_before, message_after):
        return
        await self.redisqueue.update_message(message_after)
        await self.socketio.on_message_update(message_after)

    async def on_message_delete(self, message):
        return
        self.delete_list.append(message.id)
        await self.redisqueue.delete_message(message)
        await self.socketio.on_message_delete(message)
        
    async def on_reaction_add(self, reaction, user):
        return
        await self.redisqueue.update_message(reaction.message)
        await self.socketio.on_reaction_add(reaction.message)
    
    async def on_reaction_remove(self, reaction, user):
        return
        await self.redisqueue.update_message(reaction.message)
        await self.socketio.on_reaction_remove(reaction.message)
    
    async def on_reaction_clear(self, message, reactions):
        return
        await self.redisqueue.update_message(message)
        await self.socketio.on_reaction_clear(message)

    async def on_guild_join(self, guild):
        return
        await self.redisqueue.update_guild(guild)
        await self.postStats()

    async def on_guild_remove(self, guild):
        return
        await self.redisqueue.delete_guild(guild)
        await self.postStats()

    async def on_guild_update(self, guildbefore, guildafter):
        return
        await self.redisqueue.update_guild(guildafter)
        await self.socketio.on_guild_update(guildafter)

    async def on_guild_role_create(self, role):
        return
        if role.name == self.user.name and role.managed:
            await asyncio.sleep(2)
        await self.redisqueue.update_guild(role.guild)
        await self.socketio.on_guild_role_create(role)

    async def on_guild_role_delete(self, role):
        return
        if role.guild.me not in role.guild.members:
            return
        await self.redisqueue.update_guild(role.guild)
        await self.socketio.on_guild_role_delete(role)

    async def on_guild_role_update(self, rolebefore, roleafter):
        return
        await self.redisqueue.update_guild(roleafter.guild)
        await self.socketio.on_guild_role_update(roleafter)

    async def on_guild_channel_delete(self, channel):
        return
        if channel.guild:
            await self.redisqueue.update_guild(channel.guild)
            await self.socketio.on_channel_delete(channel)

    async def on_guild_channel_create(self, channel):
        return
        if channel.guild:
            await self.redisqueue.update_guild(channel.guild)
            await self.socketio.on_channel_create(channel)

    async def on_guild_channel_update(self, channelbefore, channelafter):
        return
        await self.redisqueue.update_guild(channelafter.guild)
        await self.socketio.on_channel_update(channelafter)

    async def on_member_join(self, member):
        return
        await self.redisqueue.add_member(member)
        await self.socketio.on_guild_member_add(member)

    async def on_member_remove(self, member):
        return
        await self.redisqueue.remove_member(member)
        await self.socketio.on_guild_member_remove(member)

    async def on_member_update(self, memberbefore, memberafter):
        return
        await self.redisqueue.update_member(memberafter)
        await self.socketio.on_guild_member_update(memberafter)

    async def on_member_ban(self, guild, user):
        return
        if self.user.id == user.id:
            return
        await self.redisqueue.ban_member(guild, user)
    
    async def on_guild_emojis_update(self, guild, before, after):
        return
        await self.redisqueue.update_guild(guild)
        if len(after) == 0:
            await self.socketio.on_guild_emojis_update(before)
        else:
            await self.socketio.on_guild_emojis_update(after)
            
    # async def on_webhooks_update(self, channel):
    #     await self.redisqueue.update_guild(channel.guild)
        
    async def on_raw_message_edit(self, payload):
        return
        message_id = payload.message_id
        data = payload.data
        if not self.in_messages_cache(int(message_id)):
            channel = self.get_channel(int(data["channel_id"]))
            me = channel.guild.get_member(self.user.id)
            if channel.permissions_for(me).read_messages:
                message = await channel.fetch_message(int(message_id))
                await self.on_message_edit(None, message)
    
    async def on_raw_message_delete(self, payload):
        return
        message_id = payload.message_id
        channel_id = payload.channel_id
        if not self.in_messages_cache(int(message_id)):
            await asyncio.sleep(1)
            await self.process_raw_message_delete(int(message_id), int(channel_id))
    
    async def raw_bulk_message_delete(self, payload):
        return
        message_ids = payload.message_ids
        channel_id = payload.channel_id
        await asyncio.sleep(1)
        for msgid in message_ids:
            msgid = int(msgid)
            if not self.in_messages_cache(msgid):
                await self.process_raw_message_delete(msgid, int(channel_id))
    
    async def process_raw_message_delete(self, msg_id, channel_id):
        return
        if msg_id in self.delete_list:
            self.delete_list.remove(msg_id)
            return
        channel = self.get_channel(int(channel_id))
        data = {
            'content': "What fun is there in making sense?",
            'type': 0,
            'edited_timestamp': None,
            'id': msg_id,
            'channel_id': channel_id,
            'timestamp': '2017-01-15T02:59:58+00:00',
            'attachments': [],
            'embeds': [],
            'pinned': False,
            'mention_everyone': False,
            'tts': False,
            'nonce': None,
        }
        msg = discord.Message(channel=channel, state=self._connection, data=data) # Procreate a fake message object
        await self.on_message_delete(msg)
    
    async def on_raw_reaction_add(self, payload):
        return
        message_id = payload.message_id
        if not self.in_messages_cache(message_id):
            channel = self.get_channel(payload.channel_id)
            me = channel.guild.get_member(self.user.id)
            if channel.permissions_for(me).read_messages:
                message = await channel.fetch_message(message_id)
                if len(message.reactions):
                    await self.on_reaction_add(message.reactions[0], None)
    
    async def on_raw_reaction_remove(self, payload):
        return
        message_id = payload.message_id
        if not self.in_messages_cache(message_id):
            partial = payload.emoji
            emoji = self._connection._upgrade_partial_emoji(partial)
            channel = self.get_channel(payload.channel_id)
            me = channel.guild.get_member(self.user.id)
            if channel.permissions_for(me).read_messages:
                message = await channel.fetch_message(message_id)
                message._add_reaction({"me": payload.user_id == self.user.id}, emoji, payload.user_id)
                reaction = message._remove_reaction({}, emoji, payload.user_id)
                await self.on_reaction_remove(reaction, None)
    
    async def on_raw_reaction_clear(self, payload):
        return
        message_id = payload.message_id
        if not self.in_messages_cache(message_id):
            channel = self.get_channel(payload.channel_id)
            me = channel.guild.get_member(self.user.id)
            if channel.permissions_for(me).read_messages:
                message = await channel.fetch_message(message_id)
                await self.on_reaction_clear(message, [])
    
    async def on_socket_response(self, msg):
        return
        if "op" in msg and "t" in msg and msg["op"] == 0:
            if msg["t"] == "WEBHOOKS_UPDATE":
                guild_id = int(msg["d"]["guild_id"])
                guild = self.get_guild(guild_id)
                if guild:
                    await self.redisqueue.update_guild(guild)
    
    def in_messages_cache(self, msg_id):
        return
        for msg in self._connection._messages:
            if msg.id == msg_id:
                return True
        return False

    async def auto_post_stats(self):
        while not self.is_closed():
            await self.postStats()
            await asyncio.sleep(1800)
        
    async def postStats(self):
        count = len(self.guilds)
        shard_count = self.shard_count
        shard_id = self.shard_id
        await self.discordBotsOrg.post(count, shard_count, shard_id)
        await self.botsDiscordPw.post(count, shard_count, shard_id)
