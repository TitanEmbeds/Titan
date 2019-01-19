from titanembeds.utils import get_formatted_message, get_formatted_user, get_formatted_guild
from urllib.parse import urlparse
import asyncio_redis
import json
import discord
import asyncio
import traceback
import sys
import re

class RedisQueue:
    def __init__(self, bot, redis_uri):
        self.bot = bot
        self.redis_uri = redis_uri
    
    async def connect(self):
        url_parsed = urlparse(self.redis_uri)
        url_path = 0
        if url_parsed.path and len(url_parsed.path) > 2:
            url_path = int(url_parsed.path[1:])
        self.sub_connection = await asyncio_redis.Connection.create(
            host = url_parsed.hostname or "localhost",
            port = url_parsed.port or 6379,
            password = url_parsed.password,
            db = url_path
        )
        self.connection = await asyncio_redis.Pool.create(
            host = url_parsed.hostname or "localhost",
            port = url_parsed.port or 6379,
            password = url_parsed.password,
            db = url_path,
            poolsize = 10
        )
    
    async def subscribe(self):
        await self.bot.wait_until_ready()
        subscriber = await self.sub_connection.start_subscribe()
        await subscriber.subscribe(["discord-api-req"])
        count = 0
        while True:
            if not self.bot.is_ready() or self.bot.is_closed():
                await asyncio.sleep(0)
                continue
            reply = await subscriber.next_published()
            request = json.loads(reply.value)
            resource = request["resource"]
            self.dispatch(resource, request["key"], request["params"])
            count = count + 1
            if count > 10:
                count = 0
            elif count == 10:
                await asyncio.sleep(0)
    
    def dispatch(self, event, key, params):
        method = "on_" + event
        if hasattr(self, method):
            self.bot.loop.create_task(self._run_event(method, key, params))

    async def _run_event(self, event, key, params):
        try:
            await getattr(self, event)(key, params)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_error(event)
            except asyncio.CancelledError:
                pass

    async def on_error(self, event_method):
        print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
        traceback.print_exc()
    
    async def set_scan_json(self, key, dict_key, dict_value_pattern):
        unformatted_item = None
        formatted_item = None
        exists = await self.connection.exists(key)
        if exists:
            members = await self.connection.smembers(key)
            for member in members:
                the_member = await member
                if not the_member:
                    continue
                parsed = json.loads(the_member)
                if re.match(str(dict_value_pattern), str(parsed[dict_key])):
                    unformatted_item = the_member
                    formatted_item = parsed
                    break
        return (unformatted_item, formatted_item)
    
    async def enforce_expiring_key(self, key):
        ttl = await self.connection.ttl(key)
        newttl = 0
        if ttl == -1:
            newttl = 60 * 5 # 5 minutes
        if ttl >= 0:
            newttl = ttl
        await self.connection.expire(key, newttl)
    
    async def on_get_channel_messages(self, key, params):
        channel = self.bot.get_channel(int(params["channel_id"]))
        if not channel or not isinstance(channel, discord.channel.TextChannel):
            return
        await self.connection.delete([key])
        messages = []
        me = channel.guild.get_member(self.bot.user.id)
        if channel.permissions_for(me).read_messages:
            async for message in channel.history(limit=50):
                formatted = get_formatted_message(message)
                messages.append(json.dumps(formatted, separators=(',', ':')))
        await self.connection.sadd(key, [""] + messages)
    
    async def push_message(self, message):
        if message.guild:
            key = "Queue/channels/{}/messages".format(message.channel.id)
            exists = await self.connection.exists(key)
            if exists:
                message = get_formatted_message(message)
                await self.connection.sadd(key, [json.dumps(message, separators=(',', ':'))])
    
    async def delete_message(self, message):
        if message.guild:
            key = "Queue/channels/{}/messages".format(message.channel.id)
            exists = await self.connection.exists(key)
            if exists:
                unformatted_item, formatted_item = await self.set_scan_json(key, "id", message.id)
                if formatted_item:
                    await self.connection.srem(key, [unformatted_item])
    
    async def update_message(self, message):
        await self.delete_message(message)
        await self.push_message(message)

    async def on_get_guild_member(self, key, params):
        guild = self.bot.get_guild(int(params["guild_id"]))
        if not guild:
            await self.connection.set(key, "")
            await self.enforce_expiring_key(key)
            return
        member = guild.get_member(int(params["user_id"]))
        if not member:
            await self.connection.set(key, "")
            await self.enforce_expiring_key(key)
            return
        user = get_formatted_user(member)
        await self.connection.set(key, json.dumps(user, separators=(',', ':')))
        await self.enforce_expiring_key(key)
    
    async def on_get_guild_member_named(self, key, params):
        guild = self.bot.get_guild(int(params["guild_id"]))
        query = params["query"]
        result = None
        if guild:
            members = guild.members
        else:
            members = None
        if members and len(query) > 5 and query[-5] == '#':
            potential_discriminator = query[-4:]
            result = discord.utils.get(members, name=query[:-5], discriminator=potential_discriminator)
            if not result:
                result = discord.utils.get(members, nick=query[:-5], discriminator=potential_discriminator)
        if not result:
            result = ""
        else:
            result_id = result.id
            result = json.dumps({"user_id": result_id}, separators=(',', ':'))
            get_guild_member_key = "Queue/guilds/{}/members/{}".format(guild.id, result_id)
            get_guild_member_param = {"guild_id": guild.id, "user_id": result_id}
            await self.on_get_guild_member(get_guild_member_key, get_guild_member_param)
        await self.connection.set(key, result)
        await self.enforce_expiring_key(key)
    
    async def on_list_guild_members(self, key, params):
        guild = self.bot.get_guild(int(params["guild_id"]))
        members = guild.members
        member_ids = []
        for member in members:
            member_ids.append(json.dumps({"user_id": member.id}, separators=(',', ':')))
            get_guild_member_key = "Queue/guilds/{}/members/{}".format(guild.id, member.id)
            get_guild_member_param = {"guild_id": guild.id, "user_id": member.id}
            await self.on_get_guild_member(get_guild_member_key, get_guild_member_param)
        await self.connection.sadd(key, member_ids)
    
    async def add_member(self, member):
        key = "Queue/guilds/{}/members".format(member.guild.id)
        exists = await self.connection.exists(key)
        if exists:
            await self.connection.sadd(key, [json.dumps({"user_id": member.id}, separators=(',', ':'))])
    
    async def remove_member(self, member, guild=None):
        if not guild:
            guild = member.guild
        guild_member_key = "Queue/guilds/{}/members/{}".format(guild.id, member.id)
        list_members_key = "Queue/guilds/{}/members".format(guild.id)
        await self.connection.srem(list_members_key, [json.dumps({"user_id": member.id}, separators=(',', ':'))])
        await self.connection.delete([guild_member_key])
    
    async def update_member(self, member):
        await self.remove_member(member)
        await self.add_member(member)

    async def ban_member(self, guild, user):
        await self.remove_member(user, guild)
    
    async def on_get_guild(self, key, params):
        guild = self.bot.get_guild(int(params["guild_id"]))
        if not guild:
            await self.connection.set(key, "")
            await self.enforce_expiring_key(key)
            return
        if guild.me and guild.me.guild_permissions.manage_webhooks:
            try:
                server_webhooks = await guild.webhooks()
            except:
                server_webhooks = []
        else:
            server_webhooks = []
        guild_fmtted = get_formatted_guild(guild, server_webhooks)
        await self.connection.set(key, json.dumps(guild_fmtted, separators=(',', ':')))
        await self.enforce_expiring_key(key)
    
    async def delete_guild(self, guild):
        key = "Queue/guilds/{}".format(guild.id)
        await self.connection.delete([key])
    
    async def update_guild(self, guild):
        key = "Queue/guilds/{}".format(guild.id)
        exists = await self.connection.exists(key)
        if exists:
            await self.delete_guild(guild)
            await self.on_get_guild(key, {"guild_id": guild.id})
        await self.enforce_expiring_key(key)
    
    async def on_get_user(self, key, params):
        user = self.bot.get_user(int(params["user_id"]))
        if not user:
            await self.connection.set(key, "")
            await self.enforce_expiring_key(key)
            return
        user_formatted = {
            "id": user.id,
            "username": user.name,
            "discriminator": user.discriminator,
            "avatar": user.avatar,
            "bot": user.bot
        }
        await self.connection.set(key, json.dumps(user_formatted, separators=(',', ':')))
        await self.enforce_expiring_key(key)