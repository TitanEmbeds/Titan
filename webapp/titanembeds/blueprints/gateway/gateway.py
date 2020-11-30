from titanembeds.utils import serializer, socketio, guild_accepts_visitors, get_client_ipaddr, discord_api, check_user_in_guild, get_guild_channels, update_user_status, guild_webhooks_enabled, redis_store, redisqueue, get_forced_role
from titanembeds.database import db
from flask_socketio import Namespace, emit, disconnect, join_room, leave_room
import functools
from flask import request, session
import time
import json
import os

class Gateway(Namespace):
    def teardown_db_session(self):
        db.session.commit()
        db.session.remove()

    def on_connect(self):
        gateway_identifier = os.environ.get("TITAN_GATEWAY_ID", None)
        emit('hello', {"gateway_identifier": gateway_identifier})

    def on_identify(self, data):
        authorization = data.get("session", None)
        if authorization:
            try:
                data = serializer.loads(authorization)
                session.update(data)
            except:
                pass
        guild_id = data["guild_id"]
        if not guild_accepts_visitors(guild_id) and not check_user_in_guild(guild_id):
            disconnect()
            self.teardown_db_session()
            return
        session["socket_guild_id"] = guild_id
        channels = []
        forced_role = get_forced_role(guild_id)
        if guild_accepts_visitors(guild_id) and not check_user_in_guild(guild_id):
            channels = get_guild_channels(guild_id, force_everyone=True, forced_role=forced_role)
        else:
            channels = get_guild_channels(guild_id, forced_role=forced_role)
        join_room("GUILD_"+guild_id)
        for chan in channels:
            if chan["read"]:
                join_room("CHANNEL_"+chan["channel"]["id"])
        if session.get("unauthenticated", True) and guild_id in session.get("user_keys", {}):
            join_room("IP_"+get_client_ipaddr())
        elif not session.get("unauthenticated", True):
            join_room("USER_"+str(session["user_id"]))
        visitor_mode = data["visitor_mode"]
        if not visitor_mode:
            if session["unauthenticated"]:
                emit("embed_user_connect", {"unauthenticated": True, "username": session["username"], "discriminator": session["user_id"]}, room="GUILD_"+guild_id)
            else:
                nickname = redisqueue.get_guild_member(guild_id, session["user_id"]).get("nickname")
                emit("embed_user_connect", {"unauthenticated": False, "id": str(session["user_id"]), "nickname": nickname, "username": session["username"],"discriminator": session["discriminator"], "avatar_url": session["avatar"]}, room="GUILD_"+guild_id)
        emit("identified")
        self.teardown_db_session()

    def on_disconnect(self):
        if "user_keys" not in session:
            self.teardown_db_session()
            return
        if "socket_guild_id" not in session:
            self.teardown_db_session()
            return
        else:
            guild_id = session["socket_guild_id"]
            msg = {}
            if session["unauthenticated"]:
                msg = {"unauthenticated": True, "username": session["username"], "discriminator": session["user_id"]}
            else:
                msg = {"unauthenticated": False, "id": str(session["user_id"])}
            emit("embed_user_disconnect", msg, room="GUILD_"+guild_id)
            if guild_webhooks_enabled(guild_id): # Delete webhooks
                guild_webhooks = redisqueue.get_guild(guild_id)["webhooks"]
                name = "[Titan] "
                username = session["username"]
                if len(username) > 19:
                    username = username[:19]
                if session["unauthenticated"]:
                    name = name + username + "#" + str(session["user_id"])
                else:
                    name = name + username + "#" + str(session["discriminator"])
                for webhook in guild_webhooks:
                    if webhook["name"] == name:
                        discord_api.delete_webhook(webhook["id"], webhook["token"])
        self.teardown_db_session()

    def on_heartbeat(self, data):
        if "socket_guild_id" not in session:
            disconnect()
            return
        guild_id = data["guild_id"]
        visitor_mode = data["visitor_mode"]
        if not visitor_mode:
            key = None
            if "unauthenticated" not in session:
                self.teardown_db_session()
                disconnect()
                return
            if session["unauthenticated"]:
                key = session["user_keys"][guild_id]
            status = update_user_status(guild_id, session["username"], key)
            if status["revoked"] or status["banned"]:
                emit("revoke")
                self.teardown_db_session()
                time.sleep(1)
                disconnect()
                return
            else:
                emit("ack")
        else:
            if not guild_accepts_visitors(guild_id):
                self.teardown_db_session()
                disconnect()
                return
        self.teardown_db_session()

    def on_channel_list(self, data):
        if "socket_guild_id" not in session:
            disconnect()
            return
        guild_id = data["guild_id"]
        visitor_mode = data["visitor_mode"]
        channels = None
        forced_role = get_forced_role(guild_id)
        if visitor_mode or session.get("unauthenticated", True):
            channels = get_guild_channels(guild_id, True, forced_role=forced_role)
        else:
            channels = get_guild_channels(guild_id, forced_role=forced_role)
        for chan in channels:
            if chan["read"]:
                join_room("CHANNEL_"+chan["channel"]["id"])
            else:
                leave_room("CHANNEL_"+chan["channel"]["id"])
        emit("channel_list", channels)
        self.teardown_db_session()

    def on_current_user_info(self, data):
        if "socket_guild_id" not in session:
            disconnect()
            return
        guild_id = data["guild_id"]
        if "user_keys" in session and not session["unauthenticated"]:
            dbMember = redisqueue.get_guild_member(guild_id, session["user_id"])
            usr = {
                'avatar': session["avatar"],
                'username': dbMember.get("username"),
                'nickname': dbMember.get("nickname"),
                'discriminator': dbMember.get("discriminator"),
                'user_id': str(session['user_id']),
            }
            emit("current_user_info", usr)
        self.teardown_db_session()

    def get_user_color(self, guild_id, user_id):
        color = None
        member = redisqueue.get_guild_member(guild_id, user_id)
        if not member:
            return None
        guild_roles = redisqueue.get_guild(guild_id)["roles"]
        guildroles_filtered = {}
        for role in guild_roles:
            guildroles_filtered[role["id"]] = role
        member_roleids = member["roles"]
        member_roles = []
        for roleid in member_roleids:
            role = guildroles_filtered.get(str(roleid))
            if not role:
                continue
            member_roles.append(role)
        member_roles = sorted(member_roles, key=lambda k: k['position'])
        for role in member_roles:
            if role["color"] != 0:
                color = '{0:02x}'.format(role["color"])
                while len(color) < 6:
                    color = "0" + color
        return color

    def on_lookup_user_info(self, data):
        if "socket_guild_id" not in session:
            disconnect()
            return
        guild_id = data["guild_id"]
        name = data["name"]
        discriminator = data["discriminator"]
        usr = {
            "name": name,
            "id": None,
            "username": None,
            "nickname": None,
            "discriminator": discriminator,
            "avatar": None,
            "color": None,
            "avatar_url": None,
            "discordbotsorgvoted": False,
        }
        member = redisqueue.get_guild_member_named(guild_id, "{}#{}".format(name, discriminator))
        if member:
            usr["id"] = str(member["id"])
            usr["username"] = member["username"]
            usr["nickname"] = member["nick"]
            usr["avatar"] = member["avatar"]
            usr["color"] = self.get_user_color(guild_id, usr["id"])
            if (usr["avatar"]):
                usr["avatar_url"] = "https://cdn.discordapp.com/avatars/{}/{}.png".format(usr["id"], usr["avatar"])
            usr["roles"] = member["roles"]
            usr["discordbotsorgvoted"] = bool(redis_store.get("DiscordBotsOrgVoted/" + str(member["id"])))
        else:
            member = redisqueue.get_guild_member_named(guild_id, name)
            if member:
                usr["id"] = str(member["id"])
                usr["username"] = member["username"]
                usr["nickname"] = member["nick"]
                usr["avatar"] = member["avatar"]
                usr["color"] = self.get_user_color(guild_id, usr["id"])
                if (usr["avatar"]):
                    usr["avatar_url"] = "https://cdn.discordapp.com/avatars/{}/{}.png".format(usr["id"], usr["avatar"])
                usr["roles"] = member["roles"]
                usr["discordbotsorgvoted"] = bool(redis_store.get("DiscordBotsOrgVoted/" + str(member["id"])))
        emit("lookup_user_info", usr)
        self.teardown_db_session()
