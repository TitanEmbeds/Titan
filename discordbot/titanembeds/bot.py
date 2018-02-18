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
logging.basicConfig(filename='titanbot.log',level=logging.INFO,format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
handler = logging.FileHandler(config.get("logging-location", "titanbot.log"))
logging.getLogger('TitanBot')
logging.getLogger('sqlalchemy')

class Titan(discord.Client):
    def __init__(self):
        super().__init__(max_messages=20000)
        self.aiosession = aiohttp.ClientSession(loop=self.loop)
        self.http.user_agent += ' TitanEmbeds-Bot'
        self.database = DatabaseInterface(self)
        self.command = Commands(self, self.database)
        self.socketio = SocketIOInterface(self, config["redis-uri"])
        
        self.delete_list = [] # List of msg ids to prevent duplicate delete
        
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

        await self.change_presence(
            game=discord.Game(name="Embed your Discord server! Visit https://TitanEmbeds.com/"), status=discord.Status.online
        )

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

        # if "no-init" not in sys.argv:
        #     for server in self.servers:
        #         await self.database.update_guild(server)
        #         if server.large:
        #             await self.request_offline_members(server)
        #         if server.me.server_permissions.ban_members:
        #             server_bans = await self.get_bans(server)
        #         else:
        #             server_bans = []
        #         for member in server.members:
        #             banned = member.id in [u.id for u in server_bans]
        #             await self.database.update_guild_member(
        #                 member,
        #                 True,
        #                 banned
        #             )
        #         await self.database.flag_unactive_guild_members(server.id, server.members)
        #         await self.database.flag_unactive_bans(server.id, server_bans)
        #     await self.database.remove_unused_guilds(self.servers)
        # else:
        #     print("Skipping indexing server due to no-init flag")

    async def on_message(self, message):
        await self.socketio.on_message(message)
        await self.database.push_message(message)

        msg_arr = message.content.split() # split the message
        if len(message.content.split()) > 1 and message.server: #making sure there is actually stuff in the message and have arguments and check if it is sent in server (not PM)
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

    async def on_server_join(self, guild):
        await self.database.update_guild(guild)
        for member in guild.members:
            await self.database.update_guild_member(member, True, False)
        if guild.me.server_permissions.ban_members:
            banned = await self.get_bans(guild)
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
            chanperm = channel.permissions_for(channel.server.me)
            if not chanperm.read_messages or not chanperm.read_message_history:
                continue
            async for message in self.logs_from(channel, limit=50, reverse=True):
                try:
                    await self.database.push_message(message)
                except:
                    pass
        await self.postStats()

    async def on_server_remove(self, guild):
        await self.database.remove_guild(guild)
        await self.postStats()

    async def on_server_update(self, guildbefore, guildafter):
        await self.database.update_guild(guildafter)
        await self.socketio.on_guild_update(guildafter)

    async def on_server_role_create(self, role):
        if role.name == self.user.name and role.managed:
            await asyncio.sleep(2)
        await self.database.update_guild(role.server)
        await self.socketio.on_guild_role_create(role)

    async def on_server_role_delete(self, role):
        if role.server.me not in role.server.members:
            return
        await self.database.update_guild(role.server)
        await self.socketio.on_guild_role_delete(role)

    async def on_server_role_update(self, rolebefore, roleafter):
        await self.database.update_guild(roleafter.server)
        await self.socketio.on_guild_role_update(roleafter)

    async def on_channel_delete(self, channel):
        if channel.server:
            await self.database.update_guild(channel.server)
            await self.socketio.on_channel_delete(channel)

    async def on_channel_create(self, channel):
        if channel.server:
            await self.database.update_guild(channel.server)
            await self.socketio.on_channel_create(channel)

    async def on_channel_update(self, channelbefore, channelafter):
        await self.database.update_guild(channelafter.server)
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

    async def on_member_unban(self, server, user):
        await self.database.unban_server_user(user, server)
    
    async def on_server_emojis_update(self, before, after):
        if len(after) == 0:
            await self.database.update_guild(before[0].server)
            await self.socketio.on_guild_emojis_update(before)
        else:
            await self.database.update_guild(after[0].server)
            await self.socketio.on_guild_emojis_update(after)
            
    async def on_webhooks_update(self, server):
        await self.database.update_guild(server)

    async def on_socket_raw_receive(self, msg):
        if type(msg) is not str:
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
        channel = self.get_channel(channel_id)
        msg = discord.Message(channel=channel, reactions=[], id=msg_id, type=0, timestamp="2017-01-15T02:59:58", content="What fun is there in making sense?") # Procreate a fake message object
        await self.on_message_delete(msg)
    
    def in_messages_cache(self, msg_id):
        for msg in self.messages:
            if msg.id == msg_id:
                return True
        return False
        
    async def postStats(self):
        count = len(self.servers)
        await self.discordBotsOrg.post(count)
        await self.botsDiscordPw.post(count)
