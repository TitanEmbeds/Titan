import requests
import sys
import time
import json
from titanembeds.utils import redis_store
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
        self.user_agent = "TitanEmbeds (https://github.com/TitanEmbeds/Titan) Python/{} requests/{}".format(sys.version_info, requests.__version__)

    def init_discordrest(self):
        if not self._bucket_contains("global_limited"):
            self._set_bucket("global_limited", False)
            self._set_bucket("global_limit_expire", 0)

    def _get_bucket(self, key):
        value = redis_store.get(self.global_redis_prefix + key)
        if value:
            value = value
        return value

    def _set_bucket(self, key, value):
        return redis_store.set(self.global_redis_prefix + key, value)

    def _bucket_contains(self, key):
        return redis_store.exists(self.global_redis_prefix + key)

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
                time.sleep(int(float(self._get_bucket("global_limit_expire"))) - curepoch)
                curepoch = time.time()

            if self._bucket_contains(url) and float(int(self._get_bucket(url))) > curepoch:
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

    def create_message(self, channel_id, content):
        _endpoint = "/channels/{channel_id}/messages".format(channel_id=channel_id)
        payload = {'content': content}
        r = self.request("POST", _endpoint, data=payload)
        return r

    #####################
    # Guild
    #####################

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
    
    def get_guild_member(self, guild_id, user_id):
        _endpoint = "/guilds/{guild_id}/members/{user_id}".format(guild_id=guild_id, user_id=user_id)
        r = self.request("GET", _endpoint)
        return r

    def modify_guild_embed(self, guild_id, **kwargs):
        _endpoint = "/guilds/{guild_id}/embed".format(guild_id=guild_id)
        r = self.request("PATCH", _endpoint, data=kwargs, json=True)
        return r

    #####################
    # Widget Handler
    #####################

    def get_widget(self, guild_id):
        _endpoint = _DISCORD_API_BASE + "/servers/{guild_id}/widget.json".format(guild_id=guild_id)
        embed = self.get_guild_embed(guild_id)
        if not embed.get("success", True):
            return {"success": False}
        if not embed['content']['enabled']:
            self.modify_guild_embed(guild_id, enabled=True, channel_id=guild_id)
        widget = requests.get(_endpoint).json()
        return widget
    
    
    #####################
    # Webhook
    #####################
    
    def create_webhook(self, channel_id, name, avatar=None):
        _endpoint = "/channels/{channel_id}/webhooks".format(channel_id=channel_id)
        payload = {
            "name": name,
        }
        if avatar:
            payload["avatar"] = avatar
        r = self.request("POST", _endpoint, data=payload, json=True)
        return r
    
    def execute_webhook(self, webhook_id, webhook_token, username, avatar, content, wait=True):
        _endpoint = "/webhooks/{id}/{token}".format(id=webhook_id, token=webhook_token)
        if wait:
            _endpoint += "?wait=true"
        payload = {
            'content': content,
            'avatar_url': avatar,
            'username': username
        }
        r = self.request("POST", _endpoint, data=payload)
        return r
    
    def delete_webhook(self, webhook_id, webhook_token):
        _endpoint = "/webhooks/{id}/{token}".format(id=webhook_id, token=webhook_token)
        r = self.request("DELETE", _endpoint)
        return r