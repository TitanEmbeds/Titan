from flask import Blueprint, request, redirect, jsonify, abort, session
from requests_oauthlib import OAuth2Session
from config import config

user = Blueprint("user", __name__)
redirect_url = config['app-base-url'] + "/user/callback"
authorize_url = "https://discordapp.com/api/oauth2/authorize"
token_url = "https://discordapp.com/api/oauth2/token"
avatar_base_url = "https://cdn.discordapp.com/avatars/"

def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=config['client-id'],
        token=token,
        state=state,
        scope=scope,
        redirect_uri=redirect_url,
    )

def get_current_user():
    token = session['discord_token']
    discord = make_session(token=token)
    req = discord.get("https://discordapp.com/api/users/@me")
    if req.status_code != 200:
        abort(req.status_code)
    user = req.json()
    return user

@user.route("/login_authenticated", methods=["GET"])
def login_authenticated():
    scope = ['identify', 'guilds', 'guilds.join']
    discord = make_session(scope=scope)
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
        return "state error"
    discord = make_session(state=state)
    discord_token = discord.fetch_token(
        token_url,
        client_secret=config['client-secret'],
        authorization_response=request.url)
    if not discord_token:
        return "no discord token"
    session['discord_token'] = discord_token
    return str(discord_token)

@user.route('/logout', methods=["GET"])
def logout():
    session.clear()
    return "logged out"

@user.route('/me')
def me():
    return jsonify(user=get_current_user())

@user.route('/avatar')
def avatar():
    user = get_current_user()
    return avatar_base_url + str(user['id']) + '/' + str(user['avatar']) + '.jpg'
