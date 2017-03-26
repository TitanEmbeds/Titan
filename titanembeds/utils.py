from titanembeds.discordrest import DiscordREST
from flask import request, session
from flask.ext.cache import Cache
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
    sess = session.get("cachestring", None)
    if not sess:
        rand_str = lambda n: ''.join([random.choice(string.lowercase) for i in xrange(n)])
        session['cachestring'] = rand_str(25)
        sess = session['cachestring']
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
