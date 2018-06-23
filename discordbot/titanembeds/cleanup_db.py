from titanembeds.database.guilds import Guilds
from titanembeds.database.messages import Messages
import logging
import json
import random

class CleanupDatabase:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.logger = logging.getLogger("titan_cleanupdb")
        
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler("titan_cleanupdb.log")
        fh.setLevel(logging.DEBUG)
        session_id = str(random.randrange(100))
        formatter = logging.Formatter("%(asctime)s - {0} - %(levelname)s - %(message)s".format(session_id))
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.info("Initialized Database Cleaning Class with session id of " + session_id)
    
    async def start_cleanup(self):
        self.logger.info("Started cleaning up task")
        self.logger.info("Cleaning up unused guilds")
        await self.db.remove_unused_guilds(list(self.bot.guilds))
        self.logger.info("Started cleaning up messages task, hopefully cleaned up unused guilds")
        self.bot.loop.run_in_executor(None, self._start_cleanup)
    
    def _start_cleanup(self):
        with self.db.get_session() as session:
            guilds = session.query(Guilds).all()
            count = 0
            for guild in guilds:
                count += 1
                self.logger.info("[{}] snowflake-{} name-{}".format(count, guild.guild_id, guild.name))
                try:
                    channelsjson = json.loads(guild.channels)
                except:
                    continue
                active_channels = []
                for channel in channelsjson:
                    chanid = channel["id"]
                    active_channels.append(chanid)
                    keep_these = session.query(Messages.message_id).filter(Messages.channel_id == chanid).order_by(Messages.timestamp.desc()).limit(50)
                    d = session.query(Messages).filter(Messages.channel_id == chanid, ~Messages.message_id.in_(keep_these)).delete(synchronize_session=False)
                    session.commit()
                    self.logger.info("    --{} [{}]".format(channel["name"], d))
                d = session.query(Messages).filter(Messages.guild_id == guild.guild_id, ~Messages.channel_id.in_(active_channels)).delete(synchronize_session=False)
                session.commit()
                self.logger.info("    INACTIVE {}".format(d))
            self.logger.info("done!")