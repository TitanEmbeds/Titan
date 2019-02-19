from titanembeds.utils import redis_store
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
        while (not data and data != "") and loop_count < 50:
            if loop_count % 25 == 0:
                redis_store.publish("discord-api-req", json.dumps(payload))
            time.sleep(0.1)
            data = self._get(key, data_type)
            loop_count += 1
        redis_store.expire(key, 60 * 5)
        if data == None or data == "":
            return None
        if data_type == "set":
            data = list(data)
            data_parsed = []
            for d in data:
                if d != "":
                    data_parsed.append(json.loads(d))
            return data_parsed
        return json.loads(data)
    
    def _get(self, key, data_type):
        if data_type == "set":
            return redis_store.smembers(key)
        else:
            return redis_store.get(key)
            
    def validate_not_none(self, key, data_key, data):
        if data[data_key] == None:
            redis_store.delete(key)
            time.sleep(0.5)
            return False
        return True
    
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
                "reactions": x["reactions"],
                "type": x.get("type", 0),
            }
            if message["author"]["id"] not in guild_members:
                member = self.get_guild_member(guild_id, message["author"]["id"])
                guild_members[message["author"]["id"]] = member
            else:
                member = guild_members[message["author"]["id"]]
            message["author"]["nickname"] = None
            if member:
                message["author"]["nickname"] = member["nick"]
                message["author"]["avatar"] = member["avatar"]
                message["author"]["discriminator"] = member["discriminator"]
                message["author"]["username"] = member["username"]
            for mention in message["mentions"]:
                if mention["id"] not in guild_members:
                    author = self.get_guild_member(guild_id, mention["id"])
                    guild_members[mention["id"]] = author
                else:
                    author = guild_members[mention["id"]]
                mention["nickname"] = None
                if author:
                    mention["nickname"] = author["nick"]
                    mention["avatar"] = author["avatar"]
                    mention["username"] = author["username"]
                    mention["discriminator"] = author["discriminator"]
            msgs.append(message)
        sorted_msgs = sorted(msgs, key=lambda k: k['id'], reverse=True) 
        return sorted_msgs[:50] # only return last 50 messages in cache please

    def get_guild_member(self, guild_id, user_id):
        key = "/guilds/{}/members/{}".format(guild_id, user_id)
        q = self.get(key, "get_guild_member", {"guild_id": guild_id, "user_id": user_id})
        if q and not self.validate_not_none(key, "username", q):
            return self.get_user(user_id)
        return q
    
    def get_guild_member_named(self, guild_id, query):
        key = "/custom/guilds/{}/member_named/{}".format(guild_id, query)
        guild_member_id = self.get(key, "get_guild_member_named", {"guild_id": guild_id, "query": query})
        if guild_member_id:
            return self.get_guild_member(guild_id, guild_member_id["user_id"])
        return None
    
    def list_guild_members(self, guild_id):
        key = "/guilds/{}/members".format(guild_id)
        member_ids = self.get(key, "list_guild_members", {"guild_id": guild_id}, data_type="set")
        members = []
        for member_id in member_ids:
            usr_id = member_id["user_id"]
            member = self.get_guild_member(guild_id, usr_id)
            if member:
                members.append(member)
        return members
    
    def get_guild(self, guild_id):
        key = "/guilds/{}".format(guild_id)
        q = self.get(key, "get_guild", {"guild_id": guild_id})
        if q and not self.validate_not_none(key, "name", q):
            return self.get_guild(guild_id)
        return q
    
    def get_user(self, user_id):
        key = "/users/{}".format(user_id)
        q = self.get(key, "get_user", {"user_id": user_id})
        if q and not self.validate_not_none(key, "username", q):
            return self.get_user(user_id)
        return q