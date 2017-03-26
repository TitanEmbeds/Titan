from titanembeds.discordrest import DiscordREST
from flask import request, session
from flask.ext.cache import Cache
from flask_limiter import Limiter
from config import config
import random
import string

discord_api = DiscordREST(config['bot-token'])
cache = Cache()

def get_client_ipaddr():
    if hasattr(request.headers, "X-Real-IP"): # pythonanywhere specific
        return request.headers['X-Real-IP']
    else: # general
        return request.remote_addr

def generate_session_key():
    sess = session.get("sessionunique", None)
    if not sess:
        rand_str = lambda n: ''.join([random.choice(string.lowercase) for i in xrange(n)])
        session['sessionunique'] = rand_str(25)
        sess = session['sessionunique']
    return sess #Totally unique

def make_cache_key(*args, **kwargs):
    path = request.path
    args = str(hash(frozenset(request.args.items())))
    ip = get_client_ipaddr()
    sess = generate_session_key()
    return (path + args + sess + ip).encode('utf-8')

def make_guilds_cache_key():
    sess = generate_session_key()
    ip = get_client_ipaddr()
    return (sess + ip + "user_guilds").encode('utf-8')

def channel_ratelimit_key(): # Generate a bucket with given channel & unique session key
    sess = generate_session_key()
    channel_id = request.args.get('channel_id', "0")
    return (sess + channel_id).encode('utf-8')

def guild_ratelimit_key():
    sess = generate_session_key()
    guild_id = request.args.get('guild_id', "0")
    return (sess + guild_id).encode('utf-8')


rate_limiter = Limiter(key_func=get_client_ipaddr) # Default limit by ip address
