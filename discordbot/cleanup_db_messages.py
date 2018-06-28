from config import config
from titanembeds.database import DatabaseInterface, Guilds, Messages
import asyncio
import sys
import logging
import json
import gc
import random
from asyncio_extras import threadpool
logging.basicConfig(filename='titanbot.log',level=logging.INFO,format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.getLogger('TitanBot')
logging.getLogger('sqlalchemy')

###########################
#   Cleanup DB Messages   #
#                         #
# Cleans the database     #
# messages store          #
###########################

class TitanCleanupDB:
    def __init__(self):
        super().__init__()
        self.loop = asyncio.get_event_loop()
        self.database = DatabaseInterface(self)
        self.logger = logging.getLogger("titan_cleanupdb")
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler("titan_cleanupdb.log")
        fh.setLevel(logging.DEBUG)
        session_id = str(random.randrange(100))
        formatter = logging.Formatter("%(asctime)s - {0} - %(levelname)s - %(message)s".format(session_id))
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(formatter)
        self.logger.addHandler(consoleHandler)
        self.logger.info("Initialized Database Cleaning Class with session id of " + session_id)

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

    def run(self):
        try:
            self.loop.run_until_complete(self.start_cleanup())
        except Exception as e:
            print("Error!", e)
        finally:
            try:
                self._cleanup()
            except Exception as e:
                print("Error in cleanup:", e)
            self.loop.close()

    async def start_cleanup(self):
        print('Titan [DiscordBot] [UTILITY: Cleanup database messages]')
        print('------')

        try:
            self.database.connect(config["database-uri"])
        except Exception:
            self.logger.error("Unable to connect to specified database!")
            traceback.print_exc()
            return

        print("working on this...")
        with self.database.get_session() as session:
            guilds = session.query(Guilds).all()
            guilds_new = []
            count = 0
            for guild in guilds:
                guilds_new.append(guild)
            for guild in guilds_new:
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

def main():
    print("Starting...")
    te = TitanCleanupDB()
    te.run()
    gc.collect()

if __name__ == '__main__':
    main()
