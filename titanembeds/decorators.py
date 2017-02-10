from functools import wraps
from flask import url_for, redirect, session, jsonify

def valid_session_required(api=False):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'unauthenticated' not in session or 'user_id' not in session or 'username' not in session:
                session.clear()
                if api:
                    return jsonify(error=True, message="Unauthenticated session"), 403
                redirect(url_for('index'))
            if session['unauthenticated'] and 'user_keys' not in session:
                session['user_keys'] = {}
            return f(*args, **kwargs)
        return decorated_function
    return decorator
