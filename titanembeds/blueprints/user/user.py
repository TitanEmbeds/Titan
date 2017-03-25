from flask import Blueprint, request, redirect, jsonify, abort, session, url_for, render_template
from requests_oauthlib import OAuth2Session
from config import config
from titanembeds.decorators import discord_users_only
from titanembeds.utils import discord_api

user = Blueprint("user", __name__)
redirect_url = config['app-base-url'] + "/user/callback"
authorize_url = "https://discordapp.com/api/oauth2/authorize"
token_url = "https://discordapp.com/api/oauth2/token"
avatar_base_url = "https://cdn.discordapp.com/avatars/"
guild_icon_url = "https://cdn.discordapp.com/icons/"

def make_authenticated_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=config['client-id'],
        token=token,
        state=state,
        scope=scope,
        redirect_uri=url_for("user.callback", _external=True),
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

def get_user_guilds():
    req = discordrest_from_user("/users/@me/guilds")
    return req

def get_user_managed_servers():
    guilds = get_user_guilds().json()
    filtered = []
    for guild in guilds:
        permission = guild['permissions'] # Manage Server, Ban Members, Kick Members
        if guild['owner'] or user_has_permission(permission, 5) or user_has_permission(permission, 2) or user_has_permission(permission, 1):
            filtered.append(guild)
    return filtered

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
        return redirect(session["redirect"])
    return redirect(url_for("user.dashboard"))

@user.route('/logout', methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("index"))

@user.route("/dashboard")
@discord_users_only()
def dashboard():
    return render_template("dashboard.html.jinja2", servers=get_user_managed_servers(), icon_generate=generate_guild_icon_url)

@user.route("/administrate_guild/<guild_id>")
@discord_users_only()
def administrate_guild(guild_id):
    guild = discord_api.get_guild(guild_id)
    if guild['code'] == 403:
        return redirect(generate_bot_invite_url(guild_id))
    return str(guild)

@user.route('/me')
@discord_users_only()
def me():
    return jsonify(user=get_current_authenticated_user())
