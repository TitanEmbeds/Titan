from flask import Blueprint, url_for, redirect, session, render_template, abort, request
from functools import wraps
from titanembeds.database import db, get_administrators_list, Cosmetics, Guilds
from titanembeds.oauth import generate_guild_icon_url

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

@admin.route("/administrate_guild/<guild_id>", methods=["GET"])
@is_admin
def administrate_guild(guild_id):
    db_guild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    session["redirect"] = None
    permissions=[]
    permissions.append("Manage Embed Settings")
    permissions.append("Ban Members")
    permissions.append("Kick Members")
    all_members = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id).order_by(UnauthenticatedUsers.last_timestamp).all()
    all_bans = db.session.query(UnauthenticatedBans).filter(UnauthenticatedBans.guild_id == guild_id).all()
    users = prepare_guild_members_list(all_members, all_bans)
    dbguild_dict = {
        "id": db_guild.guild_id,
        "name": db_guild.name,
        "unauth_users": db_guild.unauth_users,
        "visitor_view": db_guild.visitor_view,
        "chat_links": db_guild.chat_links,
        "bracket_links": db_guild.bracket_links,
        "mentions_limit": db_guild.mentions_limit,
        "icon": db_guild.icon,
        "discordio": db_guild.discordio if db_guild.discordio != None else ""
    }
    return render_template("administrate_guild.html.j2", guild=dbguild_dict, members=users, permissions=permissions)

@admin.route("/administrate_guild/<guild_id>", methods=["POST"])
@is_admin
def update_administrate_guild(guild_id):
    db_guild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    db_guild.unauth_users = request.form.get("unauth_users", db_guild.unauth_users) in ["true", True]
    db_guild.visitor_view = request.form.get("visitor_view", db_guild.visitor_view) in ["true", True]
    db_guild.chat_links = request.form.get("chat_links", db_guild.chat_links) in ["true", True]
    db_guild.bracket_links = request.form.get("bracket_links", db_guild.bracket_links) in ["true", True]
    db_guild.mentions_limit = request.form.get("mentions_limit", db_guild.mentions_limit)
    
    discordio = request.form.get("discordio", db_guild.discordio)
    if discordio and discordio.strip() == "":
        discordio = None
    db_guild.discordio = discordio
    db.session.commit()
    return jsonify(
        id=db_guild.id,
        guild_id=db_guild.guild_id,
        unauth_users=db_guild.unauth_users,
        chat_links=db_guild.chat_links,
        bracket_links=db_guild.bracket_links,
        mentions_limit=db_guild.mentions_limit,
        discordio=db_guild.discordio,
    )

@user.route("/guilds")
@is_admin
def guilds():
    guilds = db.session.query(Guilds).all()
    return render_template("admin_guilds.html.j2", servers=guilds, icon_generate=generate_guild_icon_url)
