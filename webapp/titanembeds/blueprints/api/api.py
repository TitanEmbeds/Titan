from titanembeds.database import db, Guilds, UnauthenticatedUsers, UnauthenticatedBans, AuthenticatedUsers, KeyValueProperties, GuildMembers, Messages, get_channel_messages, list_all_guild_members
from titanembeds.decorators import valid_session_required, discord_users_only
from titanembeds.utils import check_guild_existance, guild_query_unauth_users_bool, get_client_ipaddr, discord_api, rate_limiter, channel_ratelimit_key, guild_ratelimit_key
from titanembeds.oauth import user_has_permission, generate_avatar_url, check_user_can_administrate_guild
from flask import Blueprint, abort, jsonify, session, request
from sqlalchemy import and_
import random
import requests
import json
import datetime
import re
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
        banned = checkUserBanned(guild_id)
        if banned:
            return revoked
        dbUser = GuildMembers.query.filter(GuildMembers.guild_id == guild_id).filter(GuildMembers.user_id == session["user_id"]).first()
        revoked = not dbUser or not dbUser.active
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
        dbUser = GuildMembers.query.filter(GuildMembers.guild_id == guild_id).filter(GuildMembers.user_id == session["user_id"]).first()
        if not dbUser:
            banned = False
        else:
            banned = dbUser.banned
    return banned

def update_user_status(guild_id, username, user_key=None):
    if user_unauthenticated():
        ip_address = get_client_ipaddr()
        status = {
            'authenticated': False,
            'avatar': None,
            'manage_embed': False,
            'ip_address': ip_address,
            'username': username,
            'user_key': user_key,
            'guild_id': guild_id,
            'user_id': session['user_id'],
            'banned': checkUserBanned(guild_id, ip_address),
            'revoked': checkUserRevoke(guild_id, user_key),
        }
        if status['banned'] or status['revoked']:
            session['user_keys'].pop(guild_id, None)
            return status
        dbUser = UnauthenticatedUsers.query.filter(and_(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.user_key == user_key)).first()
        dbUser.bumpTimestamp()
        if dbUser.username != username or dbUser.ip_address != ip_address:
            dbUser.username = username
            dbUser.ip_address = ip_address
            db.session.commit()
    else:
        status = {
            'authenticated': True,
            'avatar': session["avatar"],
            'manage_embed': check_user_can_administrate_guild(guild_id),
            'username': username,
            'discriminator': session['discriminator'],
            'guild_id': guild_id,
            'user_id': session['user_id'],
            'banned': checkUserBanned(guild_id),
            'revoked': checkUserRevoke(guild_id)
        }
        if status['banned'] or status['revoked']:
            return status
        dbUser = db.session.query(AuthenticatedUsers).filter(and_(AuthenticatedUsers.guild_id == guild_id, AuthenticatedUsers.client_id == status['user_id'])).first()
        dbUser.bumpTimestamp()
    return status

def check_user_in_guild(guild_id):
    if user_unauthenticated():
        return guild_id in session['user_keys']
    else:
        dbUser = db.session.query(AuthenticatedUsers).filter(and_(AuthenticatedUsers.guild_id == guild_id, AuthenticatedUsers.client_id == session['user_id'])).first()
        return dbUser is not None and not checkUserRevoke(guild_id)

def format_post_content(guild_id, message):
    illegal_post = False
    illegal_reasons = []
    message = message.replace("<", "\<")
    message = message.replace(">", "\>")

    dbguild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()

    links = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message)
    if not dbguild.chat_links and len(links) > 0:
        illegal_post = True
        illegal_reasons.append("Links is not allowed.")
    elif dbguild.chat_links and not dbguild.bracket_links:
        for link in links:
            newlink = "<" + link + ">"
            message = message.replace(link, newlink)

    mention_pattern = re.compile(r'\[@[0-9]+\]')
    all_mentions = re.findall(mention_pattern, message)
    if dbguild.mentions_limit != -1 and len(all_mentions) > dbguild.mentions_limit:
        illegal_post = True
        illegal_reasons.append("Mentions is capped at the following limit: " + str(dbguild.mentions_limit))
    for match in all_mentions:
        mention = "<@" + match[2: len(match) - 1] + ">"
        message = message.replace(match, mention, 1)

    if (session['unauthenticated']):
        message = u"**[{}#{}]** {}".format(session['username'], session['user_id'], message)
    else:
        message = u"**<{}#{}>** {}".format(session['username'], session['discriminator'], message) # I would like to do a @ mention, but i am worried about notif spam
    return (message, illegal_post, illegal_reasons)

def format_everyone_mention(channel, content):
    if not channel["mention_everyone"]:
        if "@everyone" in content:
            content = content.replace("@everyone", u"@\u200Beveryone")
        if "@here" in content:
            content = content.replace("@here", u"@\u200Bhere")
    return content

def get_member_roles(guild_id, user_id):
    q = db.session.query(GuildMembers).filter(GuildMembers.guild_id == guild_id).filter(GuildMembers.user_id == user_id).first()
    return json.loads(q.roles)

def get_dbguild_channels(guild_id):
    q = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    return json.loads(q.channels)

def get_guild_channels(guild_id):
    if user_unauthenticated():
        member_roles = [guild_id] #equivilant to @everyone role
    else:
        member_roles = get_member_roles(guild_id, session['user_id'])
        if guild_id not in member_roles:
            member_roles.append(guild_id)
    dbguild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    guild_channels = json.loads(dbguild.channels)
    guild_roles = json.loads(dbguild.roles)
    guild_owner = str(dbguild.owner_id)
    result_channels = []
    for channel in guild_channels:
        if channel['type'] == "text":
            result = {"channel": channel, "read": False, "write": False, "mention_everyone": False}
            if guild_owner == session['user_id']:
                result["read"] = True
                result["write"] = True
                result["mention_everyone"] = True
                result_channels.append(result)
                continue
            channel_perm = 0

            # @everyone
            for role in guild_roles:
                if role["id"] == guild_id:
                    channel_perm |= role["permissions"]
                    continue

            # User Guild Roles
            for m_role in member_roles:
                for g_role in guild_roles:
                    if g_role["id"] == m_role:
                        channel_perm |= g_role["permissions"]
                        continue

            # If has server administrator permission
            if user_has_permission(channel_perm, 3):
                result["read"] = True
                result["write"] = True
                result["mention_everyone"] = True
                result_channels.append(result)
                continue

            denies = 0
            allows = 0

            # channel specific
            for overwrite in channel["permission_overwrites"]:
                if overwrite["type"] == "role" and overwrite["id"] in member_roles:
                    denies |= overwrite["deny"]
                    allows |= overwrite["allow"]

            channel_perm = (channel_perm & ~denies) | allows

            # member specific
            for overwrite in channel["permission_overwrites"]:
                if overwrite["type"] == "member" and overwrite["id"] == session["user_id"]:
                    channel_perm = (channel_perm & ~overwrite['deny']) | overwrite['allow']
                    break

            result["read"] = user_has_permission(channel_perm, 10)
            result["write"] = user_has_permission(channel_perm, 11)
            result["mention_everyone"] = user_has_permission(channel_perm, 17)

            # If default channel, you can read
            if channel["id"] == guild_id:
                result["read"] = True

            # If you cant read channel, you cant write in it
            if not user_has_permission(channel_perm, 10):
                result["read"] = False
                result["write"] = False
                result["mention_everyone"] = False

            result_channels.append(result)
    return sorted(result_channels, key=lambda k: k['channel']['position'])

def filter_guild_channel(guild_id, channel_id):
    channels = get_guild_channels(guild_id)
    for chan in channels:
        if chan["channel"]["id"] == channel_id:
            return chan
    return None

def get_online_discord_users(guild_id, embed):
    apimembers = list_all_guild_members(guild_id)
    apimembers_filtered = {}
    for member in apimembers:
        apimembers_filtered[member["user"]["id"]] = member
    guild_roles = json.loads(db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first().roles)
    guildroles_filtered = {}
    for role in guild_roles:
        guildroles_filtered[role["id"]] = role
    for member in embed['members']:
        apimem = apimembers_filtered.get(member["id"])
        member["hoist-role"] = None
        member["color"] = None
        if apimem:
            for roleid in reversed(apimem["roles"]):
                role = guildroles_filtered[roleid]
                if role["color"] != 0:
                    member["color"] = '{0:02x}'.format(role["color"]) #int to hex
                if role["hoist"]:
                    member["hoist-role"] = {}
                    member["hoist-role"]["name"] = role["name"]
                    member["hoist-role"]["id"] = role["id"]
                    member["hoist-role"]["position"] = role["position"]
    return embed['members']

def get_online_embed_users(guild_id):
    time_past = (datetime.datetime.now() - datetime.timedelta(seconds = 60)).strftime('%Y-%m-%d %H:%M:%S')
    unauths = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.last_timestamp > time_past, UnauthenticatedUsers.revoked == False, UnauthenticatedUsers.guild_id == guild_id).all()
    auths = db.session.query(AuthenticatedUsers).filter(AuthenticatedUsers.last_timestamp > time_past, AuthenticatedUsers.guild_id == guild_id).all()
    users = {'unauthenticated':[], 'authenticated':[]}
    for user in unauths:
        meta = {
            'username': user.username,
            'discriminator': user.discriminator,
        }
        users['unauthenticated'].append(meta)
    for user in auths:
        client_id = user.client_id
        usrdb = db.session.query(GuildMembers).filter(GuildMembers.guild_id == guild_id).filter(GuildMembers.user_id == client_id).first()
        meta = {
            'id': usrdb.user_id,
            'username': usrdb.username,
            'discriminator': usrdb.discriminator,
            'avatar_url': generate_avatar_url(usrdb.user_id, usrdb.avatar),
        }
        users['authenticated'].append(meta)
    return users

@api.route("/fetch", methods=["GET"])
@valid_session_required(api=True)
@rate_limiter.limit("2 per 2 second", key_func = channel_ratelimit_key)
def fetch():
    guild_id = request.args.get("guild_id")
    channel_id = request.args.get('channel_id')
    after_snowflake = request.args.get('after', None, type=int)
    if user_unauthenticated():
        key = session['user_keys'][guild_id]
    else:
        key = None
    status = update_user_status(guild_id, session['username'], key)
    messages = {}
    if status['banned'] or status['revoked']:
        status_code = 403
        if user_unauthenticated():
            session['user_keys'].pop(guild_id, None)
    else:
        chan = filter_guild_channel(guild_id, channel_id)
        if not chan.get("read"):
            status_code = 401
        else:
            messages = get_channel_messages(channel_id, after_snowflake)
            status_code = 200
    response = jsonify(messages=messages, status=status)
    response.status_code = status_code
    return response

@api.route("/post", methods=["POST"])
@valid_session_required(api=True)
@rate_limiter.limit("1 per 10 second", key_func = channel_ratelimit_key)
def post():
    guild_id = request.form.get("guild_id")
    channel_id = request.form.get('channel_id')
    content = request.form.get('content')
    content, illegal_post, illegal_reasons = format_post_content(guild_id, content)
    if user_unauthenticated():
        key = session['user_keys'][guild_id]
    else:
        key = None
    status = update_user_status(guild_id, session['username'], key)
    message = {}
    if illegal_post:
        status_code = 417
    if status['banned'] or status['revoked']:
        status_code = 401
    else:
        chan = filter_guild_channel(guild_id, channel_id)
        if not chan.get("write"):
            status_code = 401
        elif not illegal_post:
            content = format_everyone_mention(chan, content)
            message = discord_api.create_message(channel_id, content)
            status_code = message['code']
    response = jsonify(message=message.get('content', message), status=status, illegal_reasons=illegal_reasons)
    response.status_code = status_code
    return response

@api.route("/create_unauthenticated_user", methods=["POST"])
@rate_limiter.limit("1 per 15 minute", key_func=guild_ratelimit_key)
def create_unauthenticated_user():
    session['unauthenticated'] = True
    username = request.form['username']
    guild_id = request.form['guild_id']
    ip_address = get_client_ipaddr()
    username = username.strip()
    if len(username) < 2 or len(username) > 32:
        abort(406)
    if not all(x.isalnum() or x.isspace() or "-" == x or "_" == x for x in username):
        abort(406)
    if not check_guild_existance(guild_id):
        abort(404)
    if not guild_query_unauth_users_bool(guild_id):
        abort(401)
    if not checkUserBanned(guild_id, ip_address):
        session['username'] = username
        if 'user_id' not in session or len(str(session["user_id"])) > 4:
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
        response = jsonify(status=status)
        response.status_code = 403
        return response

@api.route("/query_guild", methods=["GET"])
@valid_session_required(api=True)
def query_guild():
    guild_id = request.args.get('guild_id')
    if check_guild_existance(guild_id):
        if check_user_in_guild(guild_id):
            widget = discord_api.get_widget(guild_id)
            channels = get_guild_channels(guild_id)
            discordmembers = get_online_discord_users(guild_id, widget)
            embedmembers = get_online_embed_users(guild_id)
            return jsonify(channels=channels, discordmembers=discordmembers, embedmembers=embedmembers, instant_invite=widget.get("instant_invite"))
        abort(403)
    abort(404)

@api.route("/create_authenticated_user", methods=["POST"])
@discord_users_only(api=True)
def create_authenticated_user():
    guild_id = request.form.get('guild_id')
    if session['unauthenticated']:
        response = jsonify(error=True)
        response.status_code = 401
        return response
    else:
        if not check_guild_existance(guild_id):
            abort(404)
        if not checkUserBanned(guild_id):
            if not check_user_in_guild(guild_id):
                discord_api.add_guild_member(guild_id, session['user_id'], session['user_keys']['access_token'])
            db_user = db.session.query(AuthenticatedUsers).filter(and_(AuthenticatedUsers.guild_id == guild_id, AuthenticatedUsers.client_id == session['user_id'])).first()
            if not db_user:
                db_user = AuthenticatedUsers(guild_id, session['user_id'])
                db.session.add(db_user)
                db.session.commit()
            status = update_user_status(guild_id, session['username'])
            return jsonify(status=status)
        else:
            status = {'banned': True}
            response = jsonify(status=status)
            response.status_code = 403
            return response

@api.route("/cleanup-db", methods=["DELETE"])
def cleanup_keyval_db():
    if request.form.get("secret", None) == config["app-secret"]:
        q = KeyValueProperties.query.filter(KeyValueProperties.expiration < datetime.datetime.now()).all()
        for m in q:
            db.session.delete(m)

        guilds = Guilds.query.all()
        for guild in guilds:
            channelsjson = json.loads(guild.channels)
            for channel in channelsjson:
                chanid = channel["id"]
                dbmsg = Messages.query.filter(Messages.channel_id == chanid).all()
                for idx, val in enumerate(dbmsg):
                    if len(dbmsg) - idx > 50:
                        db.session.delete(val)
                    else:
                        continue
        db.session.commit()
        return ('', 204)
    abort(401)
