from flask import Blueprint, request, redirect, jsonify, abort, session, url_for, render_template
from config import config
from titanembeds.decorators import discord_users_only
from titanembeds.utils import discord_api
from titanembeds.database import db, Guilds, UnauthenticatedUsers, UnauthenticatedBans
from titanembeds.oauth import authorize_url, token_url, make_authenticated_session, get_current_authenticated_user, get_user_managed_servers, check_user_can_administrate_guild, check_user_permission, generate_avatar_url, generate_guild_icon_url, generate_bot_invite_url
import time
import datetime

user = Blueprint("user", __name__)

@user.route("/login_authenticated", methods=["GET"])
def login_authenticated():
    session["redirect"] = request.args.get("redirect")
    scope = ['identify', 'guilds', 'guilds.join']
    discord = make_authenticated_session(scope=scope)
    authorization_url, state = discord.authorization_url(
        authorize_url,
        access_type="offline"
    )
    session['oauth2_state'] = state
    return redirect(authorization_url)

@user.route('/callback', methods=["GET"])
def callback():
    state = session.get('oauth2_state')
    if not state or request.values.get('error'):
        return redirect(url_for('user.logout'))
    discord = make_authenticated_session(state=state)
    discord_token = discord.fetch_token(
        token_url,
        client_secret=config['client-secret'],
        authorization_response=request.url)
    if not discord_token:
        return redirect(url_for('user.logout'))
    session['user_keys'] = discord_token
    session['unauthenticated'] = False
    user = get_current_authenticated_user()
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['discriminator'] = user['discriminator']
    session['avatar'] = generate_avatar_url(user['id'], user['avatar'])
    if session["redirect"]:
        redir = session["redirect"]
        session['redirect'] = None
        return redirect(redir)
    return redirect(url_for("user.dashboard"))

@user.route('/logout', methods=["GET"])
def logout():
    redir = session.get("redirect", None)
    session.clear()
    if redir:
        session['redirect'] = redir
        return redirect(session['redirect'])
    return redirect(url_for("index"))

@user.route("/dashboard")
@discord_users_only()
def dashboard():
    guilds = get_user_managed_servers()
    if not guilds:
        session["redirect"] = url_for("user.dashboard")
        return redirect(url_for("user.logout"))
    if session["redirect"]:
        redir = session['redirect']
        session['redirect'] = None
        return redirect(redir)
    return render_template("dashboard.html.j2", servers=guilds, icon_generate=generate_guild_icon_url)

@user.route("/administrate_guild/<guild_id>", methods=["GET"])
@discord_users_only()
def administrate_guild(guild_id):
    if not check_user_can_administrate_guild(guild_id):
        return redirect(url_for("user.dashboard"))
    guild = discord_api.get_guild(guild_id)
    if guild['code'] != 200:
        session["redirect"] = url_for("user.administrate_guild", guild_id=guild_id, _external=True)
        return redirect(generate_bot_invite_url(guild_id))
    db_guild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    if not db_guild:
        db_guild = Guilds(guild_id)
        db.session.add(db_guild)
        db.session.commit()
    permissions=[]
    if check_user_permission(guild_id, 5):
        permissions.append("Manage Embed Settings")
    if check_user_permission(guild_id, 2):
        permissions.append("Ban Members")
    if check_user_permission(guild_id, 1):
        permissions.append("Kick Members")
    all_members = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id).order_by(UnauthenticatedUsers.last_timestamp).all()
    all_bans = db.session.query(UnauthenticatedBans).filter(UnauthenticatedBans.guild_id == guild_id).all()
    users = prepare_guild_members_list(all_members, all_bans)
    dbguild_dict = {"unauth_users": db_guild.unauth_users}
    return render_template("administrate_guild.html.j2", guild=guild['content'], dbguild=dbguild_dict, members=users, permissions=permissions)

@user.route("/administrate_guild/<guild_id>", methods=["POST"])
@discord_users_only()
def update_administrate_guild(guild_id):
    if not check_user_can_administrate_guild(guild_id):
        abort(403)
    guild = discord_api.get_guild(guild_id)
    if guild['code'] != 200:
        abort(guild['code'])
    db_guild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    if db_guild is None:
        abort(400)
    db_guild.unauth_users = request.form.get("unauth_users", db_guild.unauth_users) in ["true", True]
    db.session.commit()
    return jsonify(
        id=db_guild.id,
        guild_id=db_guild.guild_id,
        unauth_users=db_guild.unauth_users,
    )

@user.route('/me')
@discord_users_only()
def me():
    return jsonify(user=get_current_authenticated_user())

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

@user.route("/ban", methods=["POST"])
@discord_users_only(api=True)
def ban_unauthenticated_user():
    guild_id = request.form.get("guild_id", None)
    user_id = request.form.get("user_id", None)
    reason = request.form.get("reason", None)
    if reason is not None:
        reason = reason.strip()
        if reason == "":
            reason = None
    if not guild_id or not user_id:
        abort(400)
    if not check_user_permission(guild_id, 2):
        abort(401)
    db_user = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.id == user_id).order_by(UnauthenticatedUsers.id.desc()).first()
    if db_user is None:
        abort(404)
    db_ban = db.session.query(UnauthenticatedBans).filter(UnauthenticatedBans.guild_id == guild_id, UnauthenticatedBans.ip_address == db_user.ip_address).first()
    if db_ban is not None:
        if db_ban.lifter_id is None:
            abort(409)
        db.session.delete(db_ban)
    db_ban = UnauthenticatedBans(guild_id, db_user.ip_address, db_user.username, db_user.discriminator, reason, session["user_id"])
    db.session.add(db_ban)
    db.session.commit()
    return ('', 204)

@user.route("/ban", methods=["DELETE"])
@discord_users_only(api=True)
def unban_unauthenticated_user():
    guild_id = request.args.get("guild_id", None)
    user_id = request.args.get("user_id", None)
    if not guild_id or not user_id:
        abort(400)
    if not check_user_permission(guild_id, 2):
        abort(401)
    db_user = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.id == user_id).order_by(UnauthenticatedUsers.id.desc()).first()
    if db_user is None:
        abort(404)
    db_ban = db.session.query(UnauthenticatedBans).filter(UnauthenticatedBans.guild_id == guild_id, UnauthenticatedBans.ip_address == db_user.ip_address).first()
    if db_ban is None:
        abort(404)
    if db_ban.lifter_id is not None:
        abort(409)
    db_ban.liftBan(session["user_id"])
    return ('', 204)

@user.route("/revoke", methods=["POST"])
@discord_users_only(api=True)
def revoke_unauthenticated_user():
    guild_id = request.form.get("guild_id", None)
    user_id = request.form.get("user_id", None)
    if not guild_id or not user_id:
        abort(400)
    if not check_user_permission(guild_id, 1):
        abort(401)
    db_user = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.id == user_id).order_by(UnauthenticatedUsers.id.desc()).first()
    if db_user is None:
        abort(404)
    if db_user.isRevoked():
        abort(409)
    db_user.revokeUser()
    return ('', 204)
