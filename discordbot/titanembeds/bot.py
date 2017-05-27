from config import config
from titanembeds.database import DatabaseInterface
import discord
from discord.ext import commands
import aiohttp
import asyncio
import sys
import logging
logging.basicConfig(filename='titanbot.log',level=logging.INFO,format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.getLogger('TitanBot')
logging.getLogger('sqlalchemy')

bot = commands.Bot(command_prefix=config['command-prefix'])
database = DatabaseInterface(bot)

def _cleanup():
    try:
        bot.loop.run_until_complete(logout())
    except: # Can be ignored
        pass
    pending = asyncio.Task.all_tasks()
    gathered = asyncio.gather(*pending)
    try:
        gathered.cancel()
        bot.loop.run_until_complete(gathered)
        gathered.exception()
    except: # Can be ignored
        pass


@bot.event
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

@bot.event
async def on_message(self, message):
    await self.database.push_message(message)
    if message.server:
        await self.process_commands(message)

@bot.event
async def on_message_edit(self, message_before, message_after):
    await self.database.update_message(message_after)

@bot.event
async def on_message_delete(self, message):
    await self.database.delete_message(message)

@bot.event
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

@bot.event
async def on_server_remove(self, guild):
    await self.database.remove_guild(guild)

@bot.event
async def on_server_update(self, guildbefore, guildafter):
    await self.database.update_guild(guildafter)

@bot.event
async def on_server_role_create(self, role):
    if role.name == self.user.name and role.managed:
        await asyncio.sleep(2)
    await self.database.update_guild(role.server)

@bot.event
async def on_server_role_delete(self, role):
    if role.server.me not in role.server.members:
        return
    await self.database.update_guild(role.server)

@bot.event
async def on_server_role_update(self, rolebefore, roleafter):
    await self.database.update_guild(roleafter.server)

@bot.event
async def on_channel_delete(self, channel):
    await self.database.update_guild(channel.server)

@bot.event
async def on_channel_create(self, channel):
    await self.database.update_guild(channel.server)

@bot.event
async def on_channel_update(self, channelbefore, channelafter):
    await self.database.update_guild(channelafter.server)

@bot.event
async def on_member_join(self, member):
    await self.database.update_guild_member(member, active=True, banned=False)

@bot.event
async def on_member_remove(self, member):
    await self.database.update_guild_member(member, active=False, banned=False)

@bot.event
async def on_member_update(self, memberbefore, memberafter):
    await self.database.update_guild_member(memberafter)

@bot.event
async def on_member_ban(self, member):
    if self.user.id == member.id:
        return
    await self.database.update_guild_member(member, active=False, banned=True)

@bot.event
async def on_member_unban(self, server, user):
    await self.database.unban_server_user(user, server)


@commands.command(pass_context=True)
async def ban(ctx, self):
    message = ctx.message
    if not message.author.server_permissions.ban_members:
        await self.send_message(message.channel, message.author.mention + " I'm sorry, but you do not have permissions to ban guest members.")
        return
    serverid = message.server.id
    content = message.content.strip()
    if len(content.split()) == 2:
        await self.send_message(message.channel, message.author.mention + " Please provide a username-query (or optionally a discriminator) to ban a guest user.\nExample: `ban Titan#0001`")
        return
    content = content.split()
    username = content[2][:content[2].find("#")] if "#" in content[2] else content[2]
    discriminator = int(content[2][content[2].find("#") + 1:]) if "#" in content[2] else None
    reason = await self.database.ban_unauth_user_by_query(message.server.id, message.author.id, username, discriminator)
    await self.send_message(message.channel, message.author.mention + " " + reason)

@commands.command(pass_context=True)
async def kick(ctx, self):
    message = ctx.message
    if not message.author.server_permissions.kick_members:
        await self.send_message(message.channel, message.author.mention + " I'm sorry, but you do not have permissions to kick guest members.")
        return
    serverid = message.server.id
    content = message.content.strip()
    if len(content.split()) == 2:
        await self.send_message(message.channel, message.author.mention + " Please provide a username-query (or optionally a discriminator) to kick a guest user.\nExample: `kick Titan#0001`")
        return
    content = content.split()
    username = content[2][:content[2].find("#")] if "#" in content[2] else content[2]
    discriminator = int(content[2][content[2].find("#") + 1:]) if "#" in content[2] else None
    reason = await self.database.revoke_unauth_user_by_query(message.server.id, username, discriminator)
    await self.send_message(message.channel, message.author.mention + " " + reason)

try:
    bot.loop.run_until_complete(bot.run(config["bot-token"]))
except discord.errors.LoginFailure:
    print("Invalid bot token in config!")
finally:
    try:
        _cleanup()
    except Exception as e:
        print("Error in cleanup:", e)
    bot.loop.close()