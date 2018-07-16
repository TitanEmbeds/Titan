from titanembeds.utils import get_formatted_message
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
        while True:
            reply = await subscriber.next_published()
            request = json.loads(reply.value)
            resource = request["resource"]
            self.dispatch(resource, request["key"], request["params"])
    
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
                parsed = json.loads(the_member)
                if re.match(str(dict_value_pattern), str(parsed[dict_key])):
                    unformatted_item = the_member
                    formatted_item = parsed
                    break
        return (unformatted_item, formatted_item)
    
    async def on_get_channel_messages(self, key, params):
        channel = self.bot.get_channel(int(params["channel_id"]))
        if not channel or not isinstance(channel, discord.channel.TextChannel):
            return
        await self.connection.delete([key])
        messages = []
        async for message in channel.history(limit=50):
            formatted = get_formatted_message(message)
            messages.append(json.dumps(formatted))
        await self.connection.sadd(key, messages)
    
    async def push_message(self, message):
        if message.guild:
            key = "Queue/channels/{}/messages".format(message.channel.id)
            exists = await self.connection.exists(key)
            if exists:
                message = get_formatted_message(message)
                await self.connection.sadd(key, [json.dumps(message)])
    
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