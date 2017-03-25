from werkzeug.contrib.cache import SimpleCache
from titanembeds.discordrest import DiscordREST
from config import config

discord_api = DiscordREST(config['bot-token'])
cache = SimpleCache()
