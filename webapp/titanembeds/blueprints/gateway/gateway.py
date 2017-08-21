from titanembeds.utils import socketio, guild_accepts_visitors, get_client_ipaddr
from titanembeds.userbookkeeping import check_user_in_guild, get_guild_channels, update_user_status
from flask_socketio import Namespace, emit, disconnect, join_room
import functools
from flask import request, session
import time

class Gateway(Namespace):
    def on_connect(self):
        emit('hello')
    
    def on_identify(self, data):
        guild_id = data["guild_id"]
        if not guild_accepts_visitors(guild_id) and not check_user_in_guild(guild_id):
            disconnect()
            return
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
        emit("identified")
    
    def on_heartbeat(self, data):
        guild_id = data["guild_id"]
        visitor_mode = data["visitor_mode"]
        if not visitor_mode:
            status = update_user_status(guild_id, session["username"], session["user_keys"][guild_id])
            if status["revoked"] or status["banned"]:
                emit("revoke")
                time.sleep(1000)
                disconnect()
        else:
            if not guild_accepts_visitors(guild_id):
                disconnect()