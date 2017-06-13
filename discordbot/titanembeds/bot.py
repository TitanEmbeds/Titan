from config import config
from titanembeds.database import DatabaseInterface
from titanembeds.commands import Commands
import discord
import aiohttp
import asyncio
import sys
import logging
logging.basicConfig(filename='titanbot.log',level=logging.INFO,format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.getLogger('TitanBot')
logging.getLogger('sqlalchemy')

class Titan(discord.Client):
    def __init__(self):
        super().__init__()
        self.aiosession = aiohttp.ClientSession(loop=self.loop)
        self.http.user_agent += ' TitanEmbeds-Bot'
        self.database = DatabaseInterface(self)
        self.command = Commands(self, self.database)
        
        self.database_connected = False
        self.loop.create_task(self.send_webserver_heartbeat())

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
    
    async def send_webserver_heartbeat(self):
        await self.wait_until_ready()
        while not self.database_connected:
            await asyncio.sleep(1) # Wait until db is connected
        last_db_conn_status = False
        while not self.is_closed:
            try:
                await self.database.send_webserver_heartbeat()
                self.database_connected = True
            except:
                self.database_connected = False
            if last_db_conn_status != self.database_connected and config.get("errorreporting-channelid"):
                error_channel = self.get_channel(config["errorreporting-channelid"])
                if self.database_connected:
                    await self.send_message(error_channel, "Titan has obtained connection to the database!")
                else:
                    await self.send_message(error_channel, "Titan has lost connection to the database! Don't panic!! We'll sort this out... hopefully soon.")
                last_db_conn_status = self.database_connected
            await asyncio.sleep(4)

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
            game=discord.Game(name="Embed your Discord server! Visit https://TitanEmbeds.tk/"), status=discord.Status.online
        )

        try:
            await self.database.connect(config["database-uri"] + "?charset=utf8mb4")
            self.database_connected = True
        except Exception:
            self.logger.error("Unable to connect to specified database!")
            traceback.print_exc()
            await self.logout()
            return

        if "no-init" not in sys.argv:
            for server in self.servers:
                await self.database.update_guild(server)
                if server.large:
                    await self.request_offline_members(server)
                server_bans = await self.get_bans(server)
                for member in server.members:
                    banned = member.id in [u.id for u in server_bans]
                    await self.database.update_guild_member(
                        member,
                        True,
                        banned
                    )
                await self.database.flag_unactive_guild_members(server.id, server.members)
                await self.database.flag_unactive_bans(server.id, server_bans)
            await self.database.remove_unused_guilds(self.servers)
        else:
            print("Skipping indexing server due to no-init flag")

    async def on_message(self, message):
        await self.database.push_message(message)

        msg_arr = message.content.split() # split the message
        if len(message.content.split()) > 1 and message.server: #making sure there is actually stuff in the message and have arguments and check if it is sent in server (not PM)
            if msg_arr[0] == "<@{}>".format(self.user.id): #make sure it is mention
                msg_cmd = msg_arr[1].lower() # get command
                cmd = getattr(self.command, msg_cmd, None) #check if cmd exist, if not its none
                if cmd: # if cmd is not none...
                    await self.send_typing(message.channel) #this looks nice
                    await getattr(self.command, msg_cmd)(message) #actually run cmd, passing in msg obj

    async def on_message_edit(self, message_before, message_after):
        await self.database.update_message(message_after)

    async def on_message_delete(self, message):
        await self.database.delete_message(message)

    async def on_server_join(self, guild):
        await asyncio.sleep(1)
        if not guild.me.server_permissions.administrator:
            await asyncio.sleep(1)
            await self.leave_server(guild)
            return

        await self.database.update_guild(guild)
        for channel in guild.channels:
            async for message in self.logs_from(channel, limit=50, reverse=True):
                await self.database.push_message(message)
        for member in guild.members:
            await self.database.update_guild_member(member, True, False)
        banned = await self.get_bans(guild)
        for ban in banned:
            await self.database.update_guild_member(ban, False, True)

    async def on_server_remove(self, guild):
        await self.database.remove_guild(guild)

    async def on_server_update(self, guildbefore, guildafter):
        await self.database.update_guild(guildafter)

    async def on_server_role_create(self, role):
        if role.name == self.user.name and role.managed:
            await asyncio.sleep(2)
        await self.database.update_guild(role.server)

    async def on_server_role_delete(self, role):
        if role.server.me not in role.server.members:
            return
        await self.database.update_guild(role.server)

    async def on_server_role_update(self, rolebefore, roleafter):
        await self.database.update_guild(roleafter.server)

    async def on_channel_delete(self, channel):
        await self.database.update_guild(channel.server)

    async def on_channel_create(self, channel):
        await self.database.update_guild(channel.server)

    async def on_channel_update(self, channelbefore, channelafter):
        await self.database.update_guild(channelafter.server)

    async def on_member_join(self, member):
        await self.database.update_guild_member(member, active=True, banned=False)

    async def on_member_remove(self, member):
        await self.database.update_guild_member(member, active=False, banned=False)

    async def on_member_update(self, memberbefore, memberafter):
        await self.database.update_guild_member(memberafter)

    async def on_member_ban(self, member):
        if self.user.id == member.id:
            return
        await self.database.update_guild_member(member, active=False, banned=True)

    async def on_member_unban(self, server, user):
        await self.database.unban_server_user(user, server)
    
    async def on_server_emojis_update(self, before, after):
        if len(after) == 0:
            await self.database.update_guild(before[0].server)
        else:
            await self.database.update_guild(after[0].server)
