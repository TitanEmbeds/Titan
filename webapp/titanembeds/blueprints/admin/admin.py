from flask import Blueprint, url_for, redirect, session, render_template, abort, request, jsonify
from functools import wraps
from titanembeds.database import db, get_administrators_list, Cosmetics, Guilds, UnauthenticatedUsers, UnauthenticatedBans, TitanTokens, TokenTransactions, get_titan_token, set_titan_token
from titanembeds.oauth import generate_guild_icon_url
import datetime

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
def prepare_guild_members_list(members, bans):
    all_users = []
    ip_pool = []
    members = sorted(members, key=lambda k: datetime.datetime.strptime(str(k.last_timestamp), "%Y-%m-%d %H:%M:%S"), reverse=True)
    for member in members:
        user = {
            "id": member.id,
            "username": member.username,
            "discrim": member.discriminator,
            "ip": member.ip_address,
            "last_visit": member.last_timestamp,
            "kicked": member.revoked,
            "banned": False,
            "banned_timestamp": None,
            "banned_by": None,
            "banned_reason": None,
            "ban_lifted_by": None,
            "aliases": [],
        }
        for banned in bans:
            if banned.ip_address == member.ip_address:
                if banned.lifter_id is None:
                    user['banned'] = True
                user["banned_timestamp"] = banned.timestamp
                user['banned_by'] = banned.placer_id
                user['banned_reason'] = banned.reason
                user['ban_lifted_by'] = banned.lifter_id
            continue
        if user["ip"] not in ip_pool:
            all_users.append(user)
            ip_pool.append(user["ip"])
        else:
            for usr in all_users:
                if user["ip"] == usr["ip"]:
                    alias = user["username"]+"#"+str(user["discrim"])
                    if len(usr["aliases"]) < 5 and alias not in usr["aliases"]:
                        usr["aliases"].append(alias)
                    continue
    return all_users

@admin.route("/administrate_guild/<guild_id>", methods=["GET"])
@is_admin
def administrate_guild(guild_id):
    db_guild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    if not db_guild:
        abort(500)
        return
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
        "webhook_messages": db_guild.webhook_messages,
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
    db_guild.webhook_messages = request.form.get("webhook_messages", db_guild.webhook_messages) in ["true", True]
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
        visitor_view=db_guild.visitor_view,
        webhook_messages=db_guild.webhook_messages,
        chat_links=db_guild.chat_links,
        bracket_links=db_guild.bracket_links,
        mentions_limit=db_guild.mentions_limit,
        discordio=db_guild.discordio,
    )

@admin.route("/guilds")
@is_admin
def guilds():
    guilds = db.session.query(Guilds).all()
    return render_template("admin_guilds.html.j2", servers=guilds, icon_generate=generate_guild_icon_url)

@admin.route("/tokens", methods=["GET"])
@is_admin
def manage_titan_tokens():
    tokeners = db.session.query(TitanTokens).all()
    donators = []
    for usr in tokeners:
        row = {
            "user_id": usr.user_id,
            "tokens": usr.tokens,
            "transactions": []
        }
        transact = db.session.query(TokenTransactions).filter(TokenTransactions.user_id == usr.user_id).all()
        for tr in transact:
            row["transactions"].append({
                "id": tr.id,
                "user_id": tr.user_id,
                "timestamp": tr.timestamp,
                "action": tr.action,
                "net_tokens": tr.net_tokens,
                "start_tokens": tr.start_tokens,
                "end_tokens": tr.end_tokens
            })
        donators.append(row)
    return render_template("admin_token_transactions.html.j2", donators=donators)

@admin.route("/tokens", methods=["POST"])
@is_admin
def post_titan_tokens():
    user_id = request.form.get("user_id", None)
    amount = request.form.get("amount", None, type=int)
    if not user_id or not amount:
        abort(400)
    if get_titan_token(user_id) != -1:
        abort(409)
    set_titan_token(user_id, amount, "NEW VIA ADMIN")
    return ('', 204)

@admin.route("/tokens", methods=["PATCH"])
@is_admin
def patch_titan_tokens():
    user_id = request.form.get("user_id", None)
    amount = request.form.get("amount", None, type=int)
    if not user_id or not amount:
        abort(400)
    if get_titan_token(user_id) == -1:
        abort(409)
    set_titan_token(user_id, amount, "MODIFY VIA ADMIN")
    return ('', 204)