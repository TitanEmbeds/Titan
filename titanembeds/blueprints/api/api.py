from titanembeds.database import db, Guilds, UnauthenticatedUsers, UnauthenticatedBans, AuthenticatedUsers
from titanembeds.decorators import valid_session_required, discord_users_only
from titanembeds.utils import get_client_ipaddr, discord_api
from flask import Blueprint, abort, jsonify, session, request
from sqlalchemy import and_
import random
import requests
import json
import time
from config import config

api = Blueprint("api", __name__)

def user_unauthenticated():
    if 'unauthenticated' in session:
        return session['unauthenticated']
    return True

def checkUserRevoke(guild_id, user_key=None):
    revoked = True #guilty until proven not revoked
    if user_unauthenticated():
        dbUser = UnauthenticatedUsers.query.filter(and_(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.user_key == user_key)).first()
        revoked = dbUser.isRevoked()
    else:
        pass # Todo: handle authenticated user revocation status
    return revoked

def checkUserBanned(guild_id, ip_address=None):
    banned = True
    if user_unauthenticated():
        dbUser = UnauthenticatedBans.query.filter(and_(UnauthenticatedBans.guild_id == guild_id, UnauthenticatedBans.ip_address == ip_address)).all()
        if not dbUser:
            banned = False
        else:
            for usr in dbUser:
                if usr.lifter_id is not None:
                    banned = False
    else:
        banned = False
        bans = discord_api(guild_id)
        for user in bans:
            if session['user_id'] == user['id']:
                return True
    return banned

def check_guild_existance(guild_id):
    dbGuild = Guilds.query.filter_by(guild_id=guild_id).first()
    if not dbGuild:
        return False
    guilds = discord_api.get_all_guilds()
    for guild in guilds:
        if guild_id == guild['id']:
            return True
    return False

def update_user_status(guild_id, username, user_key=None):
    if user_unauthenticated():
        ip_address = get_client_ipaddr()
        status = {
            'ip_address': ip_address,
            'username': username,
            'user_key': user_key,
            'guild_id': guild_id,
            'banned': checkUserBanned(guild_id, ip_address),
            'revoked': checkUserRevoke(guild_id, user_key),
        }
        if status['banned'] or status['revoked']:
            return status
        dbUser = UnauthenticatedUsers.query.filter(and_(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.user_key == user_key)).first()
        dbUser.bumpTimestamp()
        if dbUser.username != username or dbUser.ip_address != ip_address:
            dbUser.username = username
            dbUser.ip_address = ip_address
            db.session.commit()
    else:
        pass #authenticated user todo
    return status

@api.route("/fetch", methods=["GET"])
@valid_session_required(api=True)
def fetch():
    channel_id = request.args.get('channel_id')
    after_snowflake = request.args.get('after', None, type=int)
    if user_unauthenticated():
        key = session['user_keys'][channel_id]
    else:
        key = None
    status = update_user_status(channel_id, session['username'], key)
    if status['banned'] or status['revoked']:
        messages = {}
    else:
        messages = discord_api.get_channel_messages(channel_id, after_snowflake)
    return jsonify(messages=messages, status=status)

@api.route("/post", methods=["POST"])
@valid_session_required(api=True)
def post():
    channel_id = request.form.get('channel_id')
    content = request.form.get('content')
    if user_unauthenticated():
        key = session['user_keys'][channel_id]
    else:
        key = None
    status = update_user_status(channel_id, session['username'], key)
    if status['banned'] or status['revoked']:
        return jsonify(status=status)
    message = discord_api.create_message(channel_id, content)
    return jsonify(message=message, status=status)

@api.route("/create_unauthenticated_user", methods=["POST"])
def create_unauthenticated_user():
    session['unauthenticated'] = True
    username = request.form['username']
    guild_id = request.form['guild_id']
    ip_address = get_client_ipaddr()
    if not check_guild_existance(guild_id):
        abort(400)
    if not checkUserBanned(guild_id, ip_address):
        session['username'] = username
        if 'user_id' not in session:
            session['user_id'] = random.randint(0,9999)
        user = UnauthenticatedUsers(guild_id, username, session['user_id'], ip_address)
        db.session.add(user)
        db.session.commit()
        key = user.user_key
        if 'user_keys' not in session:
            session['user_keys'] = {guild_id: key}
        else:
            session['user_keys'][guild_id] = key
        status = update_user_status(guild_id, username, key)
        return jsonify(status=status)
    else:
        status = {'banned': True}
        return jsonify(status=status)

@api.route("/query_guild", methods=["GET"])
@valid_session_required(api=True)
def query_guild():
    guild_id = request.args.get('guild_id')
    return jsonify(exists=check_guild_existance(guild_id))

@api.route("/check_discord_authentication", methods=["GET"])
@discord_users_only(api=True)
def check_discord_authentication():
    if not session['unauthenticated']:
        return jsonify(error=False)
    else:
        return jsonify(error=True)
