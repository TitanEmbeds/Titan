import requests
import sys
import time
import json
from cachetools import cached, TTLCache

_DISCORD_API_BASE = "https://discordapp.com/api/v6"
get_widget_cache = TTLCache(200, 300)
guild_list_cache = TTLCache(1, 300) # Pop the list if new guilds are added

def json_or_text(response):
    text = response.text
    if response.headers['content-type'] == 'application/json':
        return response.json()
    return text

class DiscordREST:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.user_agent = "TitanEmbeds (https://github.com/EndenDragon/Titan) Python/{} requests/{}".format(sys.version_info, requests.__version__)
        self.rate_limit_bucket = {}
        self.global_limited = False
        self.global_limit_expire = 0

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
            if self.global_limited:
                time.sleep(self.global_limit_expire - curepoch)
                curepoch = time.time()

            if url in self.rate_limit_bucket and self.rate_limit_bucket[url] > curepoch:
                time.sleep(self.rate_limit_bucket[url] - curepoch)

            url_formatted = _DISCORD_API_BASE + url
            req = requests.request(verb, url_formatted, params=params, data=data, headers=headers)

            remaining = None
            if 'X-RateLimit-Remaining' in req.headers:
                remaining = req.headers['X-RateLimit-Remaining']
                if remaining == '0' and req.status_code != 429:
                    self.rate_limit_bucket[url] = int(req.headers['X-RateLimit-Reset'])

            if 300 > req.status_code >= 200:
                self.global_limited = False
                return {
                    'success': True,
                    'content': json_or_text(req),
                    'code': req.status_code,
                }

            if req.status_code == 429:
                if 'X-RateLimit-Global' not in req.headers:
                    self.rate_limit_bucket[url] = int(req.headers['X-RateLimit-Reset'])
                else:
                    self.global_limit_expire = time.time() + int(req.headers['Retry-After'])

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

    def get_guild_channels(self, guild_id):
        _endpoint = "/guilds/{guild_id}/channels".format(guild_id=guild_id)
        r = self.request("GET", _endpoint)
        return r

    def get_guild_roles(self, guild_id):
        _endpoint = "/guilds/{guild_id}/roles".format(guild_id=guild_id)
        r = self.request("GET", _endpoint)
        return r

    def get_guild_member(self, guild_id, user_id):
        _endpoint = "/guilds/{guild_id}/members/{user_id}".format(guild_id=guild_id, user_id=user_id)
        r = self.request("GET", _endpoint)
        return r

    def modify_guild_member(self, guild_id, user_id, **kwargs):
        _endpoint = "/guilds/{guild_id}/members/{user_id}".format(guild_id=guild_id, user_id=user_id)
        r = self.request("PATCH", _endpoint, data=kwargs, json=True)
        return r

    def get_guild_embed(self, guild_id):
        _endpoint = "/guilds/{guild_id}/embed".format(guild_id=guild_id)
        r = self.request("GET", _endpoint)
        return r

    def modify_guild_embed(self, guild_id, **kwargs):
        _endpoint = "/guilds/{guild_id}/embed".format(guild_id=guild_id)
        r = self.request("PATCH", _endpoint, data=kwargs, json=True)
        return r

    #####################
    # User
    #####################

    @cached(guild_list_cache)
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

    @cached(get_widget_cache)
    def get_widget(self, guild_id):
        _endpoint = _DISCORD_API_BASE + "/servers/{guild_id}/widget.json".format(guild_id=guild_id)
        embed = self.get_guild_embed(guild_id)
        if not embed['content']['enabled']:
            self.modify_guild_embed(guild_id, enabled=True, channel_id=guild_id)
        widget = requests.get(_endpoint).json()
        return widget
