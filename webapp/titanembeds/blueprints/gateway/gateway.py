from titanembeds.utils import socketio, guild_accepts_visitors, get_client_ipaddr, discord_api, check_user_in_guild, get_guild_channels, update_user_status, guild_webhooks_enabled
from titanembeds.database import db, GuildMembers, get_guild_member, Guilds
from flask_socketio import Namespace, emit, disconnect, join_room, leave_room
import functools
from flask import request, session
import time
import json

class Gateway(Namespace):
    def on_connect(self):
        emit('hello')
    
    def on_identify(self, data):
        guild_id = data["guild_id"]
        if not guild_accepts_visitors(guild_id) and not check_user_in_guild(guild_id):
            disconnect()
            return
        session["socket_guild_id"] = guild_id
        channels = []
        if guild_accepts_visitors(guild_id) and not check_user_in_guild(guild_id):
            channels = get_guild_channels(guild_id, force_everyone=True)
        else:
            channels = get_guild_channels(guild_id)
        join_room("GUILD_"+guild_id)
        for chan in channels:
            if chan["read"]:
                join_room("CHANNEL_"+chan["channel"]["id"])
        if session.get("unauthenticated", True) and guild_id in session.get("user_keys", {}):
            join_room("IP_"+get_client_ipaddr())
        elif not session.get("unauthenticated", True):
            join_room("USER_"+session["user_id"])
        visitor_mode = data["visitor_mode"]
        if not visitor_mode:
            if session["unauthenticated"]:
                emit("embed_user_connect", {"unauthenticated": True, "username": session["username"], "discriminator": session["user_id"]}, room="GUILD_"+guild_id)
            else:
                nickname = db.session.query(GuildMembers).filter(GuildMembers.guild_id == guild_id, GuildMembers.user_id == session["user_id"]).first().nickname
                emit("embed_user_connect", {"unauthenticated": False, "id": session["user_id"], "nickname": nickname, "username": session["username"],"discriminator": session["discriminator"], "avatar_url": session["avatar"]}, room="GUILD_"+guild_id)
        emit("identified")
    
    def on_disconnect(self):
        if "user_keys" not in session:
            return
        guild_id = session["socket_guild_id"]
        msg = {}
        if session["unauthenticated"]:
            msg = {"unauthenticated": True, "username": session["username"], "discriminator": session["user_id"]}
        else:
            msg = {"unauthenticated": False, "id": session["user_id"]}
        emit("embed_user_disconnect", msg, room="GUILD_"+guild_id)
        if guild_webhooks_enabled(guild_id): # Delete webhooks
            dbguild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
            guild_webhooks = json.loads(dbguild.webhooks)
            name = "[Titan] "
            if session["unauthenticated"]:
                name = name + session["username"] + "#" + str(session["user_id"])
            else:
                name = name + session["username"] + "#" + str(session["discriminator"])
            for webhook in guild_webhooks:
                if webhook["name"] == name:
                    discord_api.delete_webhook(webhook["id"], webhook["token"])
    
    def on_heartbeat(self, data):
        guild_id = data["guild_id"]
        visitor_mode = data["visitor_mode"]
        if not visitor_mode:
            key = None
            if session["unauthenticated"]:
                key = session["user_keys"][guild_id]
            status = update_user_status(guild_id, session["username"], key)
            if status["revoked"] or status["banned"]:
                emit("revoke")
                time.sleep(1000)
                disconnect()
        else:
            if not guild_accepts_visitors(guild_id):
                disconnect()
    
    def on_channel_list(self, data):
        guild_id = data["guild_id"]
        visitor_mode = data["visitor_mode"]
        channels = None
        if visitor_mode or session.get("unauthenticated", True):
            channels = get_guild_channels(guild_id, True)
        else:
            channels = get_guild_channels(guild_id)
        for chan in channels:
            if chan["read"]:
                join_room("CHANNEL_"+chan["channel"]["id"])
            else:
                leave_room("CHANNEL_"+chan["channel"]["id"])
        emit("channel_list", channels)
    
    def on_current_user_info(self, data):
        guild_id = data["guild_id"]
        if "user_keys" in session and not session["unauthenticated"]:
            dbMember = get_guild_member(guild_id, session["user_id"])
            usr = {
                'avatar': session["avatar"],
                'username': dbMember.username,
                'nickname': dbMember.nickname,
                'discriminator': dbMember.discriminator,
                'user_id': session['user_id'],
            }
            emit("current_user_info", usr)