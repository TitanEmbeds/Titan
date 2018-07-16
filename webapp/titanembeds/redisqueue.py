from titanembeds.utils import redis_store
from titanembeds.database import get_guild_member
import json
import time

class RedisQueue:
    def __init__(self):
        pass # Nothing really to initialize
    
    def get(self, key, resource, params, *, data_type="str"):
        key = "Queue" + key
        data = self._get(key, data_type)
        payload = {
            "key": key,
            "resource": resource,
            "params": params
        }
        loop_count = 0
        while not data and loop_count < 10:
            if loop_count % 5 == 0:
                redis_store.publish("discord-api-req", json.dumps(payload))
            time.sleep(0.5)
            data = self._get(key, data_type)
            loop_count += 1
        redis_store.expire(key, 60 * 5)
        if data == None:
            return None
        if data_type == "set":
            data = list(data)
            data_parsed = []
            for d in data:
                data_parsed.append(json.loads(d))
            return data_parsed
        return json.loads(data)
    
    def _get(self, key, data_type):
        if data_type == "set":
            return redis_store.smembers(key)
        else:
            return redis_store.get(key)
    
    def get_channel_messages(self, guild_id, channel_id, after_snowflake=0):
        key = "/channels/{}/messages".format(channel_id)
        q = self.get(key, "get_channel_messages", {"channel_id": channel_id}, data_type="set")
        msgs = []
        snowflakes = []
        guild_members = {}
        for x in q:
            if x["id"] in snowflakes or int(x["id"]) <= int(after_snowflake):
                continue
            snowflakes.append(x["id"])
            message = {
                "attachments": x["attachments"],
                "timestamp": x["timestamp"],
                "id": x["id"],
                "edited_timestamp": x["edited_timestamp"],
                "author": x["author"],
                "content": x["content"],
                "channel_id": str(x["channel_id"]),
                "mentions": x["mentions"],
                "embeds": x["embeds"],
            }
            if message["author"]["id"] not in guild_members:
                member = get_guild_member(guild_id, message["author"]["id"])
                guild_members[message["author"]["id"]] = member
            else:
                member = guild_members[message["author"]["id"]]
            message["author"]["nickname"] = None
            if member:
                message["author"]["nickname"] = member.nickname
                message["author"]["avatar"] = member.avatar
                message["author"]["discriminator"] = member.discriminator
                message["author"]["username"] = member.username
            for mention in message["mentions"]:
                if mention["id"] not in guild_members:
                    author = get_guild_member(guild_id, mention["id"])
                    guild_members[mention["id"]] = author
                else:
                    author = guild_members[mention["id"]]
                mention["nickname"] = None
                if author:
                    mention["nickname"] = author.nickname
                    mention["avatar"] = author.avatar
                    mention["username"] = author.username
                    mention["discriminator"] = author.discriminator
            msgs.append(message)
        sorted_msgs = sorted(msgs, key=lambda k: k['id'], reverse=True) 
        return sorted_msgs