from flask import Blueprint, url_for, redirect, session, render_template, abort, request
from functools import wraps
from titanembeds.database import db, get_administrators_list, Cosmetics

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

@admin.route("/cosmetics", methods=["GET"])
@is_admin
def cosmetics():
    entries = db.session.query(Cosmetics).all()
    return render_template("admin_cosmetics.html.j2", cosmetics=entries)

@admin.route("/cosmetics", methods=["POST"])
@is_admin
def cosmetics_post():
    user_id = request.form.get("user_id", None)
    if not user_id:
        abort(400)
    css = request.form.get("css", None)
    entry = db.session.query(Cosmetics).filter(Cosmetics.user_id == user_id).first()
    if entry:
        abort(409)
    user = Cosmetics(user_id)
    if css:
        css = css.lower() == "true"
        user.css = css
    db.session.add(user)
    db.session.commit()
    return ('', 204)

@admin.route("/cosmetics", methods=["DELETE"])
@is_admin
def cosmetics_delete():
    user_id = request.form.get("user_id", None)
    if not user_id:
        abort(400)
    entry = db.session.query(Cosmetics).filter(Cosmetics.user_id == user_id).first()
    if not entry:
        abort(409)
    db.session.delete(entry)
    db.session.commit()
    return ('', 204)

@admin.route("/cosmetics", methods=["PATCH"])
@is_admin
def cosmetics_patch():
    user_id = request.form.get("user_id", None)
    if not user_id:
        abort(400)
    css = request.form.get("css", None)
    entry = db.session.query(Cosmetics).filter(Cosmetics.user_id == user_id).first()
    if not entry:
        abort(409)
    if css:
        css = css.lower() == "true"
        entry.css = css
    db.session.commit()
    return ('', 204)
    