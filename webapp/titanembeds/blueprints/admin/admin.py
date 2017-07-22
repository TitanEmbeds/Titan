from flask import Blueprint, url_for, redirect, session, render_template
from functools import wraps
from titanembeds.database import get_administrators_list

admin = Blueprint("admin", __name__)

def is_admin(f):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for("index"))
            if session['user_id'] not in get_administrators_list():
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator(f)

@admin.route("/")
@is_admin
def index():
    return render_template("admin_index.html.j2")
