from titanembeds.database import db, Guilds, UnauthenticatedUsers, UnauthenticatedBans, AuthenticatedUsers, GuildMembers, Messages, get_channel_messages, list_all_guild_members, get_guild_member, get_administrators_list, get_badges, DiscordBotsOrgTransactions
from titanembeds.decorators import valid_session_required, discord_users_only, abort_if_guild_disabled
from titanembeds.utils import check_guild_existance, guild_accepts_visitors, guild_query_unauth_users_bool, get_client_ipaddr, discord_api, rate_limiter, channel_ratelimit_key, guild_ratelimit_key, user_unauthenticated, checkUserRevoke, checkUserBanned, update_user_status, check_user_in_guild, get_guild_channels, guild_webhooks_enabled, guild_unauthcaptcha_enabled, get_member_roles, get_online_embed_user_keys, redis_store
from titanembeds.oauth import user_has_permission, generate_avatar_url, check_user_can_administrate_guild
from flask import Blueprint, abort, jsonify, session, request, url_for
from flask import current_app as app
from flask_socketio import emit
from sqlalchemy import and_
from urllib.parse import urlparse, parse_qsl, urlsplit
import random
import json
import datetime
import re
import requests
from config import config

api = Blueprint("api", __name__)

def parse_emoji(textToParse, guild_id):
    guild_emojis = get_guild_emojis(guild_id)
    for gemoji in guild_emojis:
        emoji_name = gemoji["name"]
        emoji_id = gemoji["id"]
        emoji_animated = gemoji["animated"]
        if emoji_animated:
            textToParse = textToParse.replace(":{}:".format(emoji_name), "<a:{}:{}>".format(emoji_name, emoji_id))
        else:
            textToParse = textToParse.replace(":{}:".format(emoji_name), "<:{}:{}>".format(emoji_name, emoji_id))
    return textToParse


def format_post_content(guild_id, channel_id, message, dbUser):
    illegal_post = False
    illegal_reasons = []
    message = message.replace("<", "\<")
    message = message.replace(">", "\>")
    message = parse_emoji(message, guild_id)

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
    
    if not guild_webhooks_enabled(guild_id):
        if (session['unauthenticated']):
            message = u"**[{}#{}]** {}".format(session['username'], session['user_id'], message)
        else:
            username = session['username']
            if dbUser:
                if dbUser.nickname:
                    username = dbUser.nickname
            message = u"**<{}#{}>** {}".format(username, session['discriminator'], message) # I would like to do a @ mention, but i am worried about notify spam
    return (message, illegal_post, illegal_reasons)

def format_everyone_mention(channel, content):
    if not channel["mention_everyone"]:
        if "@everyone" in content:
            content = content.replace("@everyone", u"@\u200Beveryone")
        if "@here" in content:
            content = content.replace("@here", u"@\u200Bhere")
    return content

def filter_guild_channel(guild_id, channel_id, force_everyone=False):
    channels = get_guild_channels(guild_id, force_everyone)
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
        apimem = apimembers_filtered.get(int(member["id"]))
        member["hoist-role"] = None
        member["color"] = None
        if apimem:
            mem_roles = []
            for roleid in apimem["roles"]:
                role = guildroles_filtered.get(roleid)
                if not role:
                    continue
                mem_roles.append(role)
            mem_roles = sorted(mem_roles, key=lambda k: k['position'])
            for role in mem_roles:
                if role["color"] != 0:
                    member["color"] = '{0:02x}'.format(role["color"]) #int to hex
                    while len(member["color"]) < 6:
                        member["color"] = "0" + member["color"]
                if role["hoist"]:
                    member["hoist-role"] = {}
                    member["hoist-role"]["name"] = role["name"]
                    member["hoist-role"]["id"] = role["id"]
                    member["hoist-role"]["position"] = role["position"]
    return embed['members']

def get_online_embed_users(guild_id):
    usrs = get_online_embed_user_keys(guild_id)
    unauths = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.user_key.in_(usrs["UnauthenticatedUsers"]), UnauthenticatedUsers.revoked == False, UnauthenticatedUsers.guild_id == guild_id).all() if usrs["UnauthenticatedUsers"] else []
    auths = db.session.query(AuthenticatedUsers).filter(AuthenticatedUsers.client_id.in_(usrs["AuthenticatedUsers"]), AuthenticatedUsers.guild_id == guild_id).all() if usrs["AuthenticatedUsers"] else []
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
            'id': str(usrdb.user_id),
            'username': usrdb.username,
            'nickname': usrdb.nickname,
            'discriminator': usrdb.discriminator,
            'avatar_url': generate_avatar_url(usrdb.user_id, usrdb.avatar),
        }
        users['authenticated'].append(meta)
    return users

def get_guild_emojis(guild_id):
    dbguild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    return json.loads(dbguild.emojis)

# Returns webhook url if exists and can post w/webhooks, otherwise None
def get_channel_webhook_url(guild_id, channel_id):
    if not guild_webhooks_enabled(guild_id):
        return None
    dbguild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    guild_webhooks = json.loads(dbguild.webhooks)
    name = "[Titan] "
    username = session["username"]
    if len(username) > 19:
        username = username[:19]
    if user_unauthenticated():
        name = name + username + "#" + str(session["user_id"])
    else:
        name = name + username + "#" + str(session["discriminator"])
    for webhook in guild_webhooks:
        if channel_id == webhook["channel_id"] and webhook["name"] == name:
            return {
                "id": webhook["id"],
                "token": webhook["token"]
            }
    webhook = discord_api.create_webhook(channel_id, name)
    return webhook["content"]

@api.route("/fetch", methods=["GET"])
@valid_session_required(api=True)
@abort_if_guild_disabled()
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
            session.modified = True
    else:
        chan = filter_guild_channel(guild_id, channel_id)
        if not chan:
            abort(404)
        if not chan.get("read") or chan["channel"]["type"] != "text":
            status_code = 401
        else:
            messages = get_channel_messages(guild_id, channel_id, after_snowflake)
            status_code = 200
    response = jsonify(messages=messages, status=status)
    response.status_code = status_code
    return response

@api.route("/fetch_visitor", methods=["GET"])
@abort_if_guild_disabled()
@rate_limiter.limit("2 per 2 second", key_func = channel_ratelimit_key)
def fetch_visitor():
    guild_id = request.args.get("guild_id")
    channel_id = request.args.get('channel_id')
    after_snowflake = request.args.get('after', None, type=int)
    if not guild_accepts_visitors(guild_id):
        abort(403)
    messages = {}
    chan = filter_guild_channel(guild_id, channel_id, True)
    if not chan:
        abort(404)
    if not chan.get("read") or chan["channel"]["type"] != "text":
        status_code = 401
    else:
        messages = get_channel_messages(guild_id, channel_id, after_snowflake)
        status_code = 200
    response = jsonify(messages=messages)
    response.status_code = status_code
    return response

@api.route("/post", methods=["POST"])
@valid_session_required(api=True)
@abort_if_guild_disabled()
@rate_limiter.limit("1 per 5 second", key_func = channel_ratelimit_key)
def post():
    guild_id = request.form.get("guild_id")
    channel_id = request.form.get('channel_id')
    content = request.form.get('content')
    if "user_id" in session:
        dbUser = GuildMembers.query.filter(GuildMembers.guild_id == guild_id).filter(GuildMembers.user_id == str(session['user_id'])).first()
    else:
        dbUser = None
    if user_unauthenticated():
        key = session['user_keys'][guild_id]
    else:
        key = None
    content, illegal_post, illegal_reasons = format_post_content(guild_id, channel_id, content, dbUser)
    status = update_user_status(guild_id, session['username'], key)
    message = {}
    if illegal_post:
        status_code = 417
    if status['banned'] or status['revoked']:
        status_code = 401
    else:
        chan = filter_guild_channel(guild_id, channel_id)
        if not chan.get("write") or chan["channel"]["type"] != "text":
            status_code = 401
        elif not illegal_post:
            userid = session["user_id"]
            content = format_everyone_mention(chan, content)
            webhook = get_channel_webhook_url(guild_id, channel_id)
            # if userid in get_administrators_list():
            #     content = "(Titan Dev) " + content
            if webhook:
                if (session['unauthenticated']):
                    username = session["username"] + "#" + str(session["user_id"])
                    avatar = url_for('static', filename='img/titanembeds_square.png', _external=True)
                    dbguild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
                    if dbguild:
                        icon = dbguild.guest_icon
                        if icon:
                            avatar = icon
                else:
                    username = session["username"]
                    if dbUser:
                        if dbUser.nickname:
                            username = dbUser.nickname
                    # if content.startswith("(Titan Dev) "):
                    #     content = content[12:]
                    #     username = "(Titan Dev) " + username
                    username = username + "#" + str(session['discriminator'])
                    avatar = session['avatar']
                message = discord_api.execute_webhook(webhook.get("id"), webhook.get("token"), username, avatar, content)
            else:
                message = discord_api.create_message(channel_id, content)
            status_code = message['code']
    response = jsonify(message=message.get('content', message), status=status, illegal_reasons=illegal_reasons)
    response.status_code = status_code
    return response

def verify_captcha_request(captcha_response, ip_address):
    payload = {
        "secret": config["recaptcha-secret-key"],
        "response": captcha_response,
        "remoteip": ip_address,
    }
    if app.config["DEBUG"]:
        del payload["remoteip"]
    r = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload).json()
    return r["success"]

@api.route("/create_unauthenticated_user", methods=["POST"])
@rate_limiter.limit("3 per 30 minute", key_func=guild_ratelimit_key)
@abort_if_guild_disabled()
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
    if guild_unauthcaptcha_enabled(guild_id):
        captcha_response = request.form['captcha_response']
        if not verify_captcha_request(captcha_response, request.remote_addr):
            abort(412)
    if not checkUserBanned(guild_id, ip_address):
        session['username'] = username
        if 'user_id' not in session or len(str(session["user_id"])) > 4:
            session['user_id'] = random.randint(0,9999)
        user = UnauthenticatedUsers(guild_id, username, session['user_id'], ip_address)
        db.session.add(user)
        key = user.user_key
        if 'user_keys' not in session:
            session['user_keys'] = {guild_id: key}
        else:
            session['user_keys'][guild_id] = key
        session.permanent = False
        status = update_user_status(guild_id, username, key)
        return jsonify(status=status)
    else:
        status = {'banned': True}
        response = jsonify(status=status)
        response.status_code = 403
        return response

@api.route("/change_unauthenticated_username", methods=["POST"])
@rate_limiter.limit("1 per 10 minute", key_func=guild_ratelimit_key)
@abort_if_guild_disabled()
def change_unauthenticated_username():
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
        if 'user_keys' not in session or guild_id not in session['user_keys'] or not session['unauthenticated']:
            abort(424)
        emitmsg = {"unauthenticated": True, "username": session["username"], "discriminator": session["user_id"]}
        session['username'] = username
        if 'user_id' not in session or len(str(session["user_id"])) > 4:
            session['user_id'] = random.randint(0,9999)
        user = UnauthenticatedUsers(guild_id, username, session['user_id'], ip_address)
        db.session.add(user)
        key = user.user_key
        session['user_keys'][guild_id] = key
        status = update_user_status(guild_id, username, key)
        emit("embed_user_disconnect", emitmsg, room="GUILD_"+guild_id, namespace="/gateway")
        return jsonify(status=status)
    else:
        status = {'banned': True}
        response = jsonify(status=status)
        response.status_code = 403
        return response

def get_guild_guest_icon(guild_id):
    guest_icon = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first().guest_icon
    return guest_icon if guest_icon else url_for('static', filename='img/titanembeds_square.png')

def process_query_guild(guild_id, visitor=False):
    widget = discord_api.get_widget(guild_id)
    channels = get_guild_channels(guild_id, visitor)
    if widget.get("success", True):
        discordmembers = get_online_discord_users(guild_id, widget)
    else:
        discordmembers = [{"id": 0, "color": "FFD6D6", "status": "dnd", "username": "Discord Server Widget is Currently Disabled"}]
    embedmembers = get_online_embed_users(guild_id)
    emojis = get_guild_emojis(guild_id)
    guest_icon = get_guild_guest_icon(guild_id)
    if visitor:
        for channel in channels:
            channel["write"] = False
    return jsonify(channels=channels, discordmembers=discordmembers, embedmembers=embedmembers, emojis=emojis, guest_icon=guest_icon, instant_invite=widget.get("instant_invite", None))

@api.route("/query_guild", methods=["GET"])
@valid_session_required(api=True)
@abort_if_guild_disabled()
def query_guild():
    guild_id = request.args.get('guild_id')
    if check_guild_existance(guild_id):
        if check_user_in_guild(guild_id):
            return process_query_guild(guild_id)
        abort(403)
    abort(404)

@api.route("/query_guild_visitor", methods=["GET"])
@abort_if_guild_disabled()
def query_guild_visitor():
    guild_id = request.args.get('guild_id')
    if check_guild_existance(guild_id):
        if not guild_accepts_visitors(guild_id):
            abort(403)
        return process_query_guild(guild_id, True)
    abort(404)

@api.route("/create_authenticated_user", methods=["POST"])
@discord_users_only(api=True)
@abort_if_guild_disabled()
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
                add_member = discord_api.add_guild_member(guild_id, session['user_id'], session['user_keys']['access_token'])
                if not add_member["success"]:
                    response = jsonify(add_member)
                    response.status_code = 422
                    return response
            db_user = db.session.query(AuthenticatedUsers).filter(and_(AuthenticatedUsers.guild_id == guild_id, AuthenticatedUsers.client_id == session['user_id'])).first()
            if not db_user:
                db_user = AuthenticatedUsers(guild_id, session['user_id'])
                db.session.add(db_user)
            status = update_user_status(guild_id, session['username'])
            return jsonify(status=status)
        else:
            status = {'banned': True}
            response = jsonify(status=status)
            response.status_code = 403
            return response
            
@api.route("/user/<guild_id>/<user_id>")
def user_info(guild_id, user_id):
    usr = {
        "id": None,
        "username": None,
        "nickname": None,
        "discriminator": None,
        "avatar": None,
        "avatar_url": None,
        "roles": [],
        "badges": [],
    }
    member = db.session.query(GuildMembers).filter(GuildMembers.guild_id == guild_id, GuildMembers.user_id == user_id).first()
    if member:
        usr["id"] = str(member.user_id)
        usr["username"] = member.username
        usr["nickname"] = member.nickname
        usr["discriminator"] = member.discriminator
        usr["avatar"] = member.avatar
        usr["avatar_url"] = generate_avatar_url(usr["id"], usr["avatar"], usr["discriminator"])
        roles = get_member_roles(guild_id, user_id)
        dbguild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
        guild_roles = json.loads(dbguild.roles)
        for r in roles:
            for gr in guild_roles:
                if gr["id"] == r:
                    usr["roles"].append(gr)
        usr["badges"] = get_badges(user_id)
        if redis_store.get("DiscordBotsOrgVoted/" + str(member.user_id)):
            usr["badges"].append("discordbotsorgvoted")
    return jsonify(usr)
    
@api.route("/webhook/discordbotsorg/vote", methods=["POST"])
def webhook_discordbotsorg_vote():
    incoming = request.get_json()
    client_id = incoming.get('bot')
    if config["client-id"] != client_id:
        abort(401)
    if request.headers.get("Authorization", "") != config.get("discordbotsorg-webhook-secret", ""):
        abort(403)
    user_id = incoming.get("user")
    vote_type = incoming.get("type")
    params = dict(parse_qsl(urlsplit(incoming.get("query", "")).query))
    if vote_type == "upvote":
        redis_store.set("DiscordBotsOrgVoted/" + user_id, "voted", 86400)
    else:
        redis_store.delete("DiscordBotsOrgVoted/" + user_id)
    referrer = None
    if "referrer" in params:
        try:
            referrer = int(float(params["referrer"]))
        except:
            pass
    DBLTrans = DiscordBotsOrgTransactions(int(float(user_id)), vote_type, referrer)
    db.session.add(DBLTrans)
    return ('', 204)