from config import config
from collections import deque
# from raven import Client as RavenClient
# import raven
import discord
import aiohttp
import asyncio
import sys
import logging
import json
# try:
#     raven_client = RavenClient(config["sentry-dsn"])
# except raven.exceptions.InvalidDsn:
#     pass
import traceback

intents = discord.Intents.default()
intents.members = False

class Titan(discord.AutoShardedClient):
    def __init__(self, shard_ids=None, shard_count=None):
        super().__init__(
            shard_ids=shard_ids,
            shard_count=shard_count,
            max_messages=10000,
            intents=intents,
            activity=discord.Game(name="Embed your Discord server! Visit https://TitanEmbeds.com/")
        )
        self.setup_logger(shard_ids)
        self.aiosession = aiohttp.ClientSession(loop=self.loop)
        self.http.user_agent += ' TitanEmbeds-Bot'

    def setup_logger(self, shard_ids=None):
        shard_ids = '-'.join(str(x) for x in shard_ids) if shard_ids is not None else ''
        logging.basicConfig(
            filename='titanbot{}.log'.format(shard_ids),
            level=logging.INFO,
            format='%(asctime)s %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p'
        )
        logging.getLogger('TitanBot')

    def _cleanup(self):
        try:
            self.loop.run_until_complete(self.logout())
        except: # Can be ignored
            pass
        pending = asyncio.Task.all_tasks()
        gathered = asyncio.gather(*pending)
        try:
            gathered.cancel()
            self.loop.run_until_complete(gathered)
            gathered.exception()
        except: # Can be ignored
            pass     
    
    async def start(self):
        await super().start(config["bot-token"])

    async def on_shard_ready(self, shard_id):
        logging.info('Titan [DiscordBot]')
        logging.info('Logged in as the following user:')
        logging.info(self.user.name)
        logging.info(self.user.id)
        logging.info('------')
        logging.info("Shard count: " + str(self.shard_count))
        logging.info("Shard id: "+ str(shard_id))
        logging.info("------")

    async def on_socket_raw_send(self, data):
        data = str(data)
        try:
            data = json.loads(data)
        except:
            return
        logging.info('DEBUG LOG {}'.format(data.get("op", -1)))
        logging.info('{}'.format(str(list(traceback.format_stack()))))
