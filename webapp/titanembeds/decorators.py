from functools import wraps
from flask import url_for, redirect, session, jsonify, abort, request
from titanembeds.database import list_disabled_guilds

def valid_session_required(api=False):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'unauthenticated' not in session or 'user_id' not in session or 'username' not in session:
                if api:
                    return jsonify(error=True, message="Unauthenticated session"), 401
                redirect(url_for('user.logout'))
            if session['unauthenticated'] and 'user_keys' not in session:
                session['user_keys'] = {}
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def discord_users_only(api=False):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'unauthenticated' not in session or session['unauthenticated']:
                if api:
                    return jsonify(error=True, message="Not logged in as a discord user"), 401
                return redirect(url_for("user.login_authenticated"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def abort_if_guild_disabled(*args):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            guild_id = request.args.get("guild_id", None)
            if not guild_id and len(args) > 0:
                guild_id = args[0]
            if guild_id in list_disabled_guilds():
                return ('', 423)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
    
import time
import logging
from config import config

logger = logging.getLogger('myapp')
hdlr = logging.FileHandler(config["app-location"] + "/timeit.log")
formatter = logging.Formatter('%(asctime)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.CRITICAL)
    
def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            # print('%r  %2.2f ms' % \
            #       (method.__name__, (te - ts) * 1000))
            logger.critical('%r  %2.2f ms' % \
                   (method.__name__, (te - ts) * 1000) + " " + str(session) + " " + str(request))
        return result
    return timed