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

def abort_if_guild_disabled():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            guild_id = request.args.get("guild_id", None)
            if guild_id in list_disabled_guilds():
                return ('', 423)
            return f(*args, **kwargs)
        return decorated_function
    return decorator