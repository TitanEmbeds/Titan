from flask import Blueprint, url_for
from functools import wraps

admin = Blueprint("admin", __name__)

devs = [ "138881969185357825" , "197322731115642880" ]

def is_admin():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for("index"))
            if session['user_id'] not in devs:
                return redirect(url_for("index"))
        return decorated_function
    return decorator
