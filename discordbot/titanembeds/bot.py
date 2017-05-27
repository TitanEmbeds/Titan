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
database = None
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
async def on_ready():
    print('Titan [DiscordBot]')
    print('Logged in as the following user:')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(
        game=discord.Game(name="Embed your Discord server! Visit https://TitanEmbeds.tk/"), status=discord.Status.online
    )
    try:
        await database = DatabaseInterface(bot, config["database-uri"] + "?charset=utf8mb4")
    except Exception:
        logger.error("Unable to connect to specified database!")
        traceback.print_exc()
        await bot.logout()
        return
    if "no-init" not in sys.argv:
        for server in bot.servers:
            await database.update_guild(server)
            if server.large:
                await bot.request_offline_members(server)
            server_bans = await bot.get_bans(server)
            for member in server.members:
                banned = member.id in [u.id for u in server_bans]
                await database.update_guild_member(
                    member,
                    True,
                    banned
                )
            await database.flag_unactive_guild_members(server.id, server.members)
            await database.flag_unactive_bans(server.id, server_bans)
        await database.remove_unused_guilds(bot.servers)
    else:
        print("Skipping indexing server due to no-init flag")

@bot.event
async def on_message(message):
    await database.push_message(message)
    if message.server:
        await bot.process_commands(message)

@bot.event
async def on_message_edit(message_before, message_after):
    await database.update_message(message_after)

@bot.event
async def on_message_delete(message):
    await database.delete_message(message)

@bot.event
async def on_server_join(guild):
    await asyncio.sleep(1)
    if not guild.me.server_permissions.administrator:
        await asyncio.sleep(1)
        await bot.leave_server(guild)
        return
    await database.update_guild(guild)
    for channel in guild.channels:
        async for message in bot.logs_from(channel, limit=50, reverse=True):
            await database.push_message(message)
    for member in guild.members:
        await database.update_guild_member(member, True, False)
    banned = await bot.get_bans(guild)
    for ban in banned:
        await database.update_guild_member(ban, False, True)

@bot.event
async def on_server_remove(guild):
    await database.remove_guild(guild)

@bot.event
async def on_server_update(guildbefore, guildafter):
    await database.update_guild(guildafter)

@bot.event
async def on_server_role_create(role):
    if role.name == bot.user.name and role.managed:
        await asyncio.sleep(2)
    await database.update_guild(role.server)

@bot.event
async def on_server_role_delete(role):
    if role.server.me not in role.server.members:
        return
    await database.update_guild(role.server)

@bot.event
async def on_server_role_update(rolebefore, roleafter):
    await database.update_guild(roleafter.server)

@bot.event
async def on_channel_delete(channel):
    await database.update_guild(channel.server)

@bot.event
async def on_channel_create(channel):
    await database.update_guild(channel.server)

@bot.event
async def on_channel_update(channelbefore, channelafter):
    await database.update_guild(channelafter.server)

@bot.event
async def on_member_join(member):
    await database.update_guild_member(member, active=True, banned=False)

@bot.event
async def on_member_remove(member):
    await database.update_guild_member(member, active=False, banned=False)

@bot.event
async def on_member_update(memberbefore, memberafter):
    await database.update_guild_member(memberafter)

@bot.event
async def on_member_ban(member):
    if bot.user.id == member.id:
        return
    await database.update_guild_member(member, active=False, banned=True)

@bot.event
async def on_member_unban(server, user):
    await database.unban_server_user(user, server)


@commands.command(pass_context=True)
async def ban(ctx, self):
    message = ctx.message
    if not message.author.server_permissions.ban_members:
        await bot.send_message(message.channel, message.author.mention + " I'm sorry, but you do not have permissions to ban guest members.")
        return
    serverid = message.server.id
    content = message.content.strip()
    if len(content.split()) == 2:
        await bot.send_message(message.channel, message.author.mention + " Please provide a username-query (or optionally a discriminator) to ban a guest user.\nExample: `ban Titan#0001`")
        return
    content = content.split()
    username = content[2][:content[2].find("#")] if "#" in content[2] else content[2]
    discriminator = int(content[2][content[2].find("#") + 1:]) if "#" in content[2] else None
    reason = await database.ban_unauth_user_by_query(message.server.id, message.author.id, username, discriminator)
    await bot.send_message(message.channel, message.author.mention + " " + reason)

@commands.command(pass_context=True)
async def kick(ctx, self):
    message = ctx.message
    if not message.author.server_permissions.kick_members:
        await bot.send_message(message.channel, message.author.mention + " I'm sorry, but you do not have permissions to kick guest members.")
        return
    serverid = message.server.id
    content = message.content.strip()
    if len(content.split()) == 2:
        await bot.send_message(message.channel, message.author.mention + " Please provide a username-query (or optionally a discriminator) to kick a guest user.\nExample: `kick Titan#0001`")
        return
    content = content.split()
    username = content[2][:content[2].find("#")] if "#" in content[2] else content[2]
    discriminator = int(content[2][content[2].find("#") + 1:]) if "#" in content[2] else None
    reason = await database.revoke_unauth_user_by_query(message.server.id, username, discriminator)
    await bot.send_message(message.channel, message.author.mention + " " + reason)

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