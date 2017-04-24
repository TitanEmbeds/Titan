import requests
import sys
import time
import json
from functools import partial
from titanembeds.utils import cache
from titanembeds.database import db, KeyValueProperties, get_keyvalproperty, set_keyvalproperty, ifexists_keyvalproperty
from flask import request

_DISCORD_API_BASE = "https://discordapp.com/api/v6"

def json_or_text(response):
    text = response.text
    if response.headers['content-type'] == 'application/json':
        return response.json()
    return text

class DiscordREST:
    def __init__(self, bot_token):
        self.global_redis_prefix = "discordapiratelimit/"
        self.bot_token = bot_token
        self.user_agent = "TitanEmbeds (https://github.com/EndenDragon/Titan) Python/{} requests/{}".format(sys.version_info, requests.__version__)

    def init_discordrest(self):
        if not self._bucket_contains("global_limited"):
            self._set_bucket("global_limited", False)
            self._set_bucket("global_limit_expire", 0)

    def _get_bucket(self, key):
        value = get_keyvalproperty(self.global_redis_prefix + key)
        return value

    def _set_bucket(self, key, value):
        return set_keyvalproperty(self.global_redis_prefix + key, value)

    def _bucket_contains(self, key):
        return ifexists_keyvalproperty(self.global_redis_prefix + key)

    def request(self, verb, url, **kwargs):
        headers = {
            'User-Agent': self.user_agent,
            'Authorization': 'Bot {}'.format(self.bot_token),
        }
        params = None
        if 'params' in kwargs:
            params = kwargs['params']
        data = None
        if 'data' in kwargs:
            data = kwargs['data']
        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
            data = json.dumps(data)

        for tries in range(5):
            curepoch = time.time()
            if self._get_bucket("global_limited") == "True":
                time.sleep(int(self._get_bucket("global_limit_expire")) - curepoch)
                curepoch = time.time()

            if self._bucket_contains(url) and int(self._get_bucket(url)) > curepoch:
                time.sleep(int(self._get_bucket(url)) - curepoch)

            url_formatted = _DISCORD_API_BASE + url
            req = requests.request(verb, url_formatted, params=params, data=data, headers=headers)

            remaining = None
            if 'X-RateLimit-Remaining' in req.headers:
                remaining = req.headers['X-RateLimit-Remaining']
                if remaining == '0' and req.status_code != 429:
                    self._set_bucket(url, int(req.headers['X-RateLimit-Reset']))

            if 300 > req.status_code >= 200:
                self._set_bucket("global_limited", False)
                return {
                    'success': True,
                    'content': json_or_text(req),
                    'code': req.status_code,
                }

            if req.status_code == 429:
                if 'X-RateLimit-Global' not in req.headers:
                    self._set_bucket(url, int(req.headers['X-RateLimit-Reset']))
                else:
                    self._set_bucket("global_limited", True)
                    self._set_bucket("global_limit_expire", time.time() + int(req.headers['Retry-After']))

            if req.status_code == 502 and tries <= 5:
                time.sleep(1 + tries * 2)
                continue

            if req.status_code == 403 or req.status_code == 404:
                return {
                    'success': False,
                    'code': req.status_code,
                }
        return {
            'success': False,
            'code': req.status_code,
            'content': json_or_text(req),
        }

    #####################
    # Channel
    #####################

    def get_channel_messages(self, channel_id, after_snowflake=None):
        _endpoint = "/channels/{channel_id}/messages".format(channel_id=channel_id)
        params = {}
        if after_snowflake is not None:
            params = {'after': after_snowflake}
        r = self.request("GET", _endpoint, params=params)
        return r

    def create_message(self, channel_id, content):
        _endpoint = "/channels/{channel_id}/messages".format(channel_id=channel_id)
        payload = {'content': content}
        r = self.request("POST", _endpoint, data=payload)
        return r

    #####################
    # Guild
    #####################

    def get_guild(self, guild_id):
        _endpoint = "/guilds/{guild_id}".format(guild_id=guild_id)
        r = self.request("GET", _endpoint)
        return r

    @cache.cache('get_guild_channels', expire=200)
    def get_guild_channels(self, guild_id):
        _endpoint = "/guilds/{guild_id}/channels".format(guild_id=guild_id)
        r = self.request("GET", _endpoint)
        return r

    def get_guild_roles(self, guild_id):
        _endpoint = "/guilds/{guild_id}/roles".format(guild_id=guild_id)
        r = self.request("GET", _endpoint)
        return r

    @cache.cache('get_guild_member', expire=200)
    def get_guild_member(self, guild_id, user_id):
        _endpoint = "/guilds/{guild_id}/members/{user_id}".format(guild_id=guild_id, user_id=user_id)
        r = self.request("GET", _endpoint)
        return r

    def get_guild_member_nocache(self, guild_id, user_id):
        _endpoint = "/guilds/{guild_id}/members/{user_id}".format(guild_id=guild_id, user_id=user_id)
        r = self.request("GET", _endpoint)
        return r

    def modify_guild_member(self, guild_id, user_id, **kwargs):
        _endpoint = "/guilds/{guild_id}/members/{user_id}".format(guild_id=guild_id, user_id=user_id)
        r = self.request("PATCH", _endpoint, data=kwargs, json=True)
        return r

    def add_guild_member(self, guild_id, user_id, access_token, **kwargs):
        _endpoint = "/guilds/{guild_id}/members/{user_id}".format(user_id=user_id, guild_id=guild_id)
        payload = {'access_token': access_token}
        payload.update(kwargs)
        r = self.request("PUT", _endpoint, data=payload, json=True)
        return r

    def get_guild_embed(self, guild_id):
        _endpoint = "/guilds/{guild_id}/embed".format(guild_id=guild_id)
        r = self.request("GET", _endpoint)
        return r

    def modify_guild_embed(self, guild_id, **kwargs):
        _endpoint = "/guilds/{guild_id}/embed".format(guild_id=guild_id)
        r = self.request("PATCH", _endpoint, data=kwargs, json=True)
        return r

    def get_guild_bans(self, guild_id):
        _endpoint = "/guilds/{guild_id}/bans".format(guild_id=guild_id)
        r = self.request("GET", _endpoint)
        return r

    @cache.cache('list_all_guild_members', expire=200)
    def list_all_guild_members(self, guild_id):
        _endpoint = "/guilds/{guild_id}/members".format(guild_id=guild_id)
        count = 1
        last_usrid = ""
        users = []
        params = {"limit": 1000}
        while count > 0:
            r = self.request("GET", _endpoint, params=params)
            if r["success"] == True:
                content = r["content"]
                count = len(content)
                users.extend(content)
                if count > 0:
                    params["after"] = content[-1]["user"]["id"]
            else:
                count = 0
        return users

    #####################
    # User
    #####################

    @cache.cache('get_all_guilds', expire=100)
    def get_all_guilds(self):
        _endpoint = "/users/@me/guilds"
        params = {}
        guilds = []
        count = 1 #priming the loop
        last_guild = ""
        while count > 0:
            r = self.request("GET", _endpoint, params=params)
            if r['success'] == True:
                content = r['content']
                count = len(content)
                guilds.extend(content)
                if count > 0:
                    params['after'] = content[-1]['id']
            else:
                count = 0
        return guilds

    #####################
    # Widget Handler
    #####################

    @cache.cache('get_widget', expire=200)
    def get_widget(self, guild_id):
        _endpoint = _DISCORD_API_BASE + "/servers/{guild_id}/widget.json".format(guild_id=guild_id)
        embed = self.get_guild_embed(guild_id)
        if not embed['content']['enabled']:
            self.modify_guild_embed(guild_id, enabled=True, channel_id=guild_id)
        widget = requests.get(_endpoint).json()
        return widget
