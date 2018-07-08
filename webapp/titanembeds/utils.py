from titanembeds.database import db, Guilds, UnauthenticatedUsers, UnauthenticatedBans, AuthenticatedUsers, GuildMembers, get_guild_member
from titanembeds.constants import LANGUAGES
from flask import request, session
from flask_limiter import Limiter
from flask_socketio import SocketIO, disconnect
from flask_babel import Babel
from flask_redis import FlaskRedis
from config import config
from sqlalchemy import and_
import random
import string
import hashlib
import time
import json

redis_store = FlaskRedis()

from titanembeds.discordrest import DiscordREST

discord_api = DiscordREST(config['bot-token'])

def get_client_ipaddr():
    if request.headers.getlist("X-Forwarded-For"):
       ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
       ip = request.remote_addr
    return hashlib.sha512((config['app-secret'] + ip).encode('utf-8')).hexdigest()[:15]

def generate_session_key():
    sess = session.get("sessionunique", None)
    if not sess:
        rand_str = lambda n: ''.join([random.choice(string.ascii_lowercase) for i in range(n)])
        session['sessionunique'] = rand_str(25)
        sess = session['sessionunique']
    return sess #Totally unique

def make_cache_key(*args, **kwargs):
    path = request.path
    args = str(hash(frozenset(request.args.items())))
    ip = get_client_ipaddr()
    sess = generate_session_key()
    return (path + args + sess + ip)

def make_user_cache_key(*args, **kwargs):
    ip = get_client_ipaddr()
    sess = generate_session_key()
    return (sess + ip)

def make_guilds_cache_key():
    sess = generate_session_key()
    ip = get_client_ipaddr()
    return (sess + ip + "user_guilds")

def make_guildchannels_cache_key():
    guild_id = request.values.get('guild_id', "0")
    sess = generate_session_key()
    ip = get_client_ipaddr()
    return (sess + ip + guild_id + "user_guild_channels")

def channel_ratelimit_key(): # Generate a bucket with given channel & unique session key
    sess = generate_session_key()
    channel_id = request.values.get('channel_id', "0")
    return (sess + channel_id)

def guild_ratelimit_key():
    ip = get_client_ipaddr()
    guild_id = request.values.get('guild_id', "0")
    return (ip + guild_id)

def check_guild_existance(guild_id):
    dbGuild = Guilds.query.filter_by(guild_id=guild_id).first()
    if not dbGuild:
        return False
    else:
        return True

def guild_accepts_visitors(guild_id):
    dbGuild = Guilds.query.filter_by(guild_id=guild_id).first()
    return dbGuild.visitor_view

def guild_query_unauth_users_bool(guild_id):
    dbGuild = db.session.query(Guilds).filter(Guilds.guild_id==guild_id).first()
    return dbGuild.unauth_users

def user_unauthenticated():
    if 'unauthenticated' in session:
        return session['unauthenticated']
    return True

def checkUserRevoke(guild_id, user_key=None):
    revoked = True #guilty until proven not revoked
    if user_unauthenticated():
        dbUser = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.user_key == user_key).first()
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

from titanembeds.oauth import check_user_can_administrate_guild, user_has_permission

def update_user_status(guild_id, username, user_key=None):
    if user_unauthenticated():
        ip_address = get_client_ipaddr()
        status = {
            'authenticated': False,
            'avatar': None,
            'manage_embed': False,
            'ip_address': ip_address,
            'username': username,
            'nickname': None,
            'user_key': user_key,
            'guild_id': guild_id,
            'user_id': str(session['user_id']),
            'banned': checkUserBanned(guild_id, ip_address),
            'revoked': checkUserRevoke(guild_id, user_key),
        }
        if status['banned'] or status['revoked']:
            session['user_keys'].pop(guild_id, None)
            return status
        dbUser = UnauthenticatedUsers.query.filter(and_(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.user_key == user_key)).first()
        bump_user_presence_timestamp(guild_id, "UnauthenticatedUsers", user_key)
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
            'nickname': None,
            'discriminator': session['discriminator'],
            'guild_id': guild_id,
            'user_id': str(session['user_id']),
            'banned': checkUserBanned(guild_id),
            'revoked': checkUserRevoke(guild_id)
        }
        if status['banned'] or status['revoked']:
            return status
        dbMember = get_guild_member(guild_id, status["user_id"])
        if dbMember:
            status["nickname"] = dbMember.nickname
        bump_user_presence_timestamp(guild_id, "AuthenticatedUsers", status["user_id"])
    return status

def bump_user_presence_timestamp(guild_id, user_type, client_key):
    redis_key = "MemberPresence/{}/{}/{}".format(guild_id, user_type, client_key)
    redis_store.set(redis_key, "", 15)

def get_online_embed_user_keys(guild_id="*", user_type=None):
    if not user_type:
        user_type = ["AuthenticatedUsers", "UnauthenticatedUsers"]
    else:
        user_type = [user_type]
    usrs = {}
    for utype in user_type:
        usrs[utype] = []
        keys = redis_store.keys("MemberPresence/{}/{}/*".format(guild_id, utype))
        for key in keys:
            key = str(key, "utf-8")
            client_key = key.split("/")[-1]
            usrs[utype].append(client_key)
    return usrs

def check_user_in_guild(guild_id):
    if user_unauthenticated():
        return guild_id in session.get("user_keys", {})
    else:
        dbUser = db.session.query(AuthenticatedUsers).filter(and_(AuthenticatedUsers.guild_id == guild_id, AuthenticatedUsers.client_id == session['user_id'])).first()
        return dbUser is not None and not checkUserRevoke(guild_id)

def get_member_roles(guild_id, user_id):
    q = db.session.query(GuildMembers).filter(GuildMembers.guild_id == guild_id).filter(GuildMembers.user_id == user_id).first()
    roles = [guild_id]
    if not q:
        member = discord_api.get_guild_member(guild_id, user_id)
        if member["success"]:
            roles = list(map(int, member["content"]["roles"]))
            member = GuildMembers(guild_id, user_id, member["content"]["user"]["username"], int(member["content"]["user"]["discriminator"]), member["content"].get("nick", None), member["content"]["user"]["avatar"], True, False, roles)
            db.session.add(member)
            db.session.commit()
    else:
        roles = json.loads(q.roles)
    return roles

def get_guild_channels(guild_id, force_everyone=False):
    if user_unauthenticated() or force_everyone:
        member_roles = [guild_id] #equivilant to @everyone role
    else:
        member_roles = get_member_roles(guild_id, session['user_id'])
        if guild_id not in member_roles:
            member_roles.append(guild_id)
    bot_member_roles = get_member_roles(guild_id, config["client-id"])
    if guild_id not in bot_member_roles:
        bot_member_roles.append(guild_id)
    dbguild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    guild_channels = json.loads(dbguild.channels)
    guild_roles = json.loads(dbguild.roles)
    guild_owner = str(dbguild.owner_id)
    result_channels = []
    for channel in guild_channels:
        if channel['type'] in ["text", "category"]:
            result = get_channel_permission(channel, guild_id, guild_owner, guild_roles, member_roles, str(session.get("user_id")), force_everyone)
            bot_result = get_channel_permission(channel, guild_id, guild_owner, guild_roles, bot_member_roles, config["client-id"], False)
            if not bot_result["read"]:
                result["read"] = False
            if not bot_result["write"]:
                result["write"] = False
            if not bot_result["mention_everyone"]:
                result["mention_everyone"] = False
            result_channels.append(result)
    return sorted(result_channels, key=lambda k: k['channel']['position'])

def get_channel_permission(channel, guild_id, guild_owner, guild_roles, member_roles, user_id=None, force_everyone=False):
    result = {"channel": channel, "read": False, "write": False, "mention_everyone": False}
    if not user_id:
        user_id = str(session.get("user_id"))
    if guild_owner == user_id:
        result["read"] = True
        result["write"] = True
        result["mention_everyone"] = True
        return result
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
        return result
    
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
        if overwrite["type"] == "member" and overwrite["id"] == str(session.get("user_id")):
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
    return result
    
def bot_can_create_webhooks(guild):
    perm = 0
    guild_roles = json.loads(guild.roles)
    # @everyone
    for role in guild_roles:
        if role["id"] == guild.guild_id:
            perm |= role["permissions"]
            continue
    member_roles = get_member_roles(guild.guild_id, config["client-id"])
    # User Guild Roles
    for m_role in member_roles:
        for g_role in guild_roles:
            if g_role["id"] == m_role:
                perm |= g_role["permissions"]
                continue
    if user_has_permission(perm, 3): # Admin perms override yes
        return True
    return user_has_permission(perm, 29)

def guild_webhooks_enabled(guild_id):
    dbguild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    if not dbguild.webhook_messages:
        return False
    return bot_can_create_webhooks(dbguild)

def guild_unauthcaptcha_enabled(guild_id):
    dbguild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    return dbguild.unauth_captcha
    
def language_code_list():
    codes = []
    for lang in LANGUAGES:
        codes.append(lang["code"])
    return codes

def is_int(specimen):
    try:
        int(specimen)
        return True
    except:
        return False

rate_limiter = Limiter(key_func=get_client_ipaddr) # Default limit by ip address
socketio = SocketIO(engineio_logger=config.get("engineio-logging", False))
babel = Babel()

@socketio.on_error_default  # disconnect on all errors
def default_socketio_error_handler(e):
    disconnect()
