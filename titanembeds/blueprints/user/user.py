from flask import Blueprint, request, redirect, jsonify, abort, session, url_for, render_template
from requests_oauthlib import OAuth2Session
from config import config
from titanembeds.decorators import discord_users_only
from titanembeds.utils import discord_api, cache, make_cache_key, make_guilds_cache_key
from titanembeds.database import db, Guilds, UnauthenticatedUsers, UnauthenticatedBans

user = Blueprint("user", __name__)
redirect_url = config['app-base-url'] + "/user/callback"
authorize_url = "https://discordapp.com/api/oauth2/authorize"
token_url = "https://discordapp.com/api/oauth2/token"
avatar_base_url = "https://cdn.discordapp.com/avatars/"
guild_icon_url = "https://cdn.discordapp.com/icons/"

def update_user_token(discord_token):
    session['user_keys'] = discord_token

def make_authenticated_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=config['client-id'],
        token=token,
        state=state,
        scope=scope,
        redirect_uri=url_for("user.callback", _external=True),
        auto_refresh_kwargs={
            'client_id': config['client-id'],
            'client_secret': config['client-secret'],
        },
        auto_refresh_url=token_url,
        token_updater=update_user_token,
    )

def discordrest_from_user(endpoint):
    token = session['user_keys']
    discord = make_authenticated_session(token=token)
    req = discord.get("https://discordapp.com/api/v6{}".format(endpoint))
    return req

def get_current_authenticated_user():
    req = discordrest_from_user("/users/@me")
    if req.status_code != 200:
        abort(req.status_code)
    user = req.json()
    return user

def user_has_permission(permission, index):
    return bool((int(permission) >> index) & 1)

@cache.cached(timeout=120, key_prefix=make_guilds_cache_key)
def get_user_guilds():
    req = discordrest_from_user("/users/@me/guilds")
    return req

def get_user_managed_servers():
    guilds = get_user_guilds()
    if guilds.status_code != 200:
        print(guilds.text)
        print(guilds.headers)
        abort(guilds.status_code)
    guilds = guilds.json()
    filtered = []
    for guild in guilds:
        permission = guild['permissions'] # Manage Server, Ban Members, Kick Members
        if guild['owner'] or user_has_permission(permission, 5) or user_has_permission(permission, 2) or user_has_permission(permission, 1):
            filtered.append(guild)
    filtered = sorted(filtered, key=lambda guild: guild['name'])
    return filtered

def get_user_managed_servers_safe():
    guilds = get_user_managed_servers()
    if guilds:
        return guilds
    return []

def get_user_managed_servers_id():
    guilds = get_user_managed_servers_safe()
    ids=[]
    for guild in guilds:
        ids.append(guild['id'])
    return ids

def check_user_can_administrate_guild(guild_id):
    guilds = get_user_managed_servers_id()
    return guild_id in guilds

def check_user_permission(guild_id, id):
    guilds = get_user_managed_servers_safe()
    for guild in guilds:
        if guild['id'] == guild_id:
            return user_has_permission(guild['permissions'], id)
    return False

def generate_avatar_url(id, av):
    return avatar_base_url + str(id) + '/' + str(av) + '.jpg'

def generate_guild_icon_url(id, hash):
    return guild_icon_url + str(id) + "/" + str(hash) + ".jpg"

def generate_bot_invite_url(guild_id):
    url = "https://discordapp.com/oauth2/authorize?&client_id={}&scope=bot&permissions={}&guild_id={}&response_type=code&redirect_uri={}".format(config['client-id'], '536083583', guild_id, url_for("user.dashboard", _external=True))
    return url

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
    session['avatar'] = generate_avatar_url(user['id'], user['avatar'])
    if session["redirect"]:
        redir = session["redirect"]
        session.pop('redirect', None)
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
    return render_template("dashboard.html.j2", servers=guilds, icon_generate=generate_guild_icon_url)

@user.route("/administrate_guild/<guild_id>", methods=["GET"])
@discord_users_only()
def administrate_guild(guild_id):
    if not check_user_can_administrate_guild(guild_id):
        return redirect(url_for("user.dashboard"))
    guild = discord_api.get_guild(guild_id)
    if guild['code'] != 200:
        return redirect(generate_bot_invite_url(guild_id))
    db_guild = Guilds.query.filter_by(guild_id=guild_id).first()
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
    all_members = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id).all()
    all_bans = db.session.query(UnauthenticatedBans).filter(UnauthenticatedBans.guild_id == guild_id).all()
    users = prepare_guild_members_list(all_members, all_bans)
    return render_template("administrate_guild.html.j2", guild=guild['content'], members=users, permissions=permissions)

@user.route('/me')
@discord_users_only()
def me():
    return jsonify(user=get_current_authenticated_user())

def prepare_guild_members_list(members, bans):
    all_users = []
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
        all_users.append(user)
    return all_users
