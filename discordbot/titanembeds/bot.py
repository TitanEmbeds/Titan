from config import config
from titanembeds.database import DatabaseInterface
from titanembeds.socketio import SocketIOInterface
from discord.ext import commands
import discord
import aiohttp
import asyncio
import sys
import logging
logging.basicConfig(filename='titanbot.log',level=logging.INFO,format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.getLogger('TitanBot')
logging.getLogger('sqlalchemy')

class CommandCog:
    def __init__(self, bot, database):
        self.bot = bot
        self.database = database

    @commands.command()
    async def ban(self, message):
        if not message.author.server_permissions.ban_members:
            await self.bot.reply("I'm sorry, but you do not have permissions to ban guest members.")
            return
        serverid = message.server.id
        content = message.content.strip()
        if len(content.split()) == 2:
            await self.bot.reply("Please provide a username-query (or optionally a discriminator) to ban a guest user.\nExample: `ban Titan#0001`")
            return
        content = content.split()
        username = content[2][:content[2].find("#")] if "#" in content[2] else content[2]
        discriminator = int(content[2][content[2].find("#") + 1:]) if "#" in content[2] else None
        reason = await self.database.ban_unauth_user_by_query(message.server.id, message.author.id, username, discriminator)
        await self.bot.reply(reason)

    @commands.command()
    async def kick(self, message):
        if not message.author.server_permissions.kick_members:
            await self.bot.reply("I'm sorry, but you do not have permissions to kick guest members.")
            return
        serverid = message.server.id
        content = message.content.strip()
        if len(content.split()) == 2:
            await self.bot.reply("Please provide a username-query (or optionally a discriminator) to kick a guest user.\nExample: `kick Titan#0001`")
            return
        content = content.split()
        username = content[2][:content[2].find("#")] if "#" in content[2] else content[2]
        discriminator = int(content[2][content[2].find("#") + 1:]) if "#" in content[2] else None
        reason = await self.database.revoke_unauth_user_by_query(message.server.id, username, discriminator)
        await self.bot.reply(reason)


class Titan(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, command_prefix=commands.when_mentioned, **kwargs)
        self.aiosession = aiohttp.ClientSession(loop=self.loop)
        self.http.user_agent += ' TitanEmbeds-Bot'
        self.database = DatabaseInterface(self)
        self.socketio = SocketIOInterface(self, config["redis-uri"])
        
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
    
    async def wait_until_dbonline(self):
        while not self.database_connected:
            await asyncio.sleep(1) # Wait until db is connected
    
    async def send_webserver_heartbeat(self):
        await self.wait_until_ready()
        await self.wait_until_dbonline()
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
            await asyncio.sleep(60)

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

        commands = CommandsCog(self, self.database)
        self.add_cog(commands)

        try:
            await self.database.connect(config["database-uri"])
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
        crashChar = 'ौौौौ'
        if crashChar in message.content:
            try:
                await bot.delete_message(message)
                await bot.send_message(message.channel,
                                       "**I've delete a message posted by {} because it contained characters which crashes discord. I've also banned him.**".format(
                                           message.author.name + "#" + message.author.discriminator + "(ID: " + message.author.id + ")"))
                await message.server.ban(message.author, "Causing discord to crash because of weird characters.")
            except:
                pass
            return
        await self.wait_until_dbonline()
        await self.database.push_message(message)
        await self.socketio.on_message(message)
        await self.process_commands(message)

    async def on_message_edit(self, message_before, message_after):
        await self.wait_until_dbonline()
        await self.database.update_message(message_after)
        await self.socketio.on_message_update(message_after)

    async def on_message_delete(self, message):
        await self.wait_until_dbonline()
        await self.database.delete_message(message)
        await self.socketio.on_message_delete(message)

    async def on_server_join(self, guild):
        await self.wait_until_dbonline()
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
        await self.wait_until_dbonline()
        await self.database.remove_guild(guild)

    async def on_server_update(self, guildbefore, guildafter):
        await self.wait_until_dbonline()
        await self.database.update_guild(guildafter)
        await self.socketio.on_guild_update(guildafter)

    async def on_server_role_create(self, role):
        await self.wait_until_dbonline()
        if role.name == self.user.name and role.managed:
            await asyncio.sleep(2)
        await self.database.update_guild(role.server)
        await self.socketio.on_guild_role_create(role)

    async def on_server_role_delete(self, role):
        await self.wait_until_dbonline()
        if role.server.me not in role.server.members:
            return
        await self.database.update_guild(role.server)
        await self.socketio.on_guild_role_delete(role)

    async def on_server_role_update(self, rolebefore, roleafter):
        await self.wait_until_dbonline()
        await self.database.update_guild(roleafter.server)
        await self.socketio.on_guild_role_update(roleafter)

    async def on_channel_delete(self, channel):
        await self.wait_until_dbonline()
        await self.database.update_guild(channel.server)
        await self.socketio.on_channel_delete(channel)

    async def on_channel_create(self, channel):
        await self.wait_until_dbonline()
        await self.database.update_guild(channel.server)
        await self.socketio.on_channel_create(channel)

    async def on_channel_update(self, channelbefore, channelafter):
        await self.wait_until_dbonline()
        await self.database.update_guild(channelafter.server)
        await self.socketio.on_channel_update(channelafter)

    async def on_member_join(self, member):
        await self.wait_until_dbonline()
        await self.database.update_guild_member(member, active=True, banned=False)
        await self.socketio.on_guild_member_add(member)

    async def on_member_remove(self, member):
        await self.wait_until_dbonline()
        await self.database.update_guild_member(member, active=False, banned=False)
        await self.socketio.on_guild_member_remove(member)

    async def on_member_update(self, memberbefore, memberafter):
        await self.wait_until_dbonline()
        await self.database.update_guild_member(memberafter)
        await self.socketio.on_guild_member_update(memberafter)

    async def on_member_ban(self, member):
        await self.wait_until_dbonline()
        if self.user.id == member.id:
            return
        await self.database.update_guild_member(member, active=False, banned=True)

    async def on_member_unban(self, server, user):
        await self.wait_until_dbonline()
        await self.database.unban_server_user(user, server)
    
    async def on_server_emojis_update(self, before, after):
        await self.wait_until_dbonline()
        if len(after) == 0:
            await self.database.update_guild(before[0].server)
            await self.socketio.on_guild_emojis_update(before)
        else:
            await self.database.update_guild(after[0].server)
            await self.socketio.on_guild_emojis_update(after)
            
    async def on_webhooks_update(self, server):
        await self.wait_until_dbonline()
        await self.database.update_guild(server)
