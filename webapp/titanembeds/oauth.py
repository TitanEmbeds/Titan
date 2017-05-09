from config import config
import json
from requests_oauthlib import OAuth2Session
from flask import session, abort, url_for
from titanembeds.database import get_keyvalproperty, set_keyvalproperty
from titanembeds.utils import make_user_cache_key

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

def get_user_guilds():
    cache = get_keyvalproperty("OAUTH/USERGUILDS/"+make_user_cache_key())
    if cache:
        return cache
    req = discordrest_from_user("/users/@me/guilds")
    if req.status_code != 200:
        abort(req.status_code)
    req = json.dumps(req.json())
    set_keyvalproperty("OAUTH/USERGUILDS/"+make_user_cache_key(), req, 250)
    return req

def get_user_managed_servers():
    guilds = json.loads(get_user_guilds())
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
            return user_has_permission(guild['permissions'], id) or guild['owner']
    return False

def generate_avatar_url(id, av):
    return avatar_base_url + str(id) + '/' + str(av) + '.jpg'

def generate_guild_icon_url(id, hash):
    return guild_icon_url + str(id) + "/" + str(hash) + ".jpg"

def generate_bot_invite_url(guild_id):
    url = "https://discordapp.com/oauth2/authorize?&client_id={}&scope=bot&permissions={}&guild_id={}&response_type=code&redirect_uri={}".format(config['client-id'], '536083583', guild_id, url_for("user.dashboard", _external=True))
    return url
