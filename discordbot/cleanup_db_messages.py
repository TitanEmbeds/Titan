from config import config
from titanembeds.database import DatabaseInterface, Guilds, Messages
from titanembeds.commands import Commands
import discord
import aiohttp
import asyncio
import sys
import logging
import json
import gc
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

class Titan(discord.Client):
    def __init__(self):
        super().__init__()
        self.aiosession = aiohttp.ClientSession(loop=self.loop)
        self.http.user_agent += ' TitanEmbeds-Bot'
        self.database = DatabaseInterface(self)
        self.command = Commands(self, self.database)

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
            self.loop.run_until_complete(self.start(config["bot-token"]))
        except discord.errors.LoginFailure:
            print("Invalid bot token in config!")
        finally:
            try:
                self._cleanup()
            except Exception as e:
                print("Error in cleanup:", e)
            self.loop.close()

    async def on_ready(self):
        print('Titan [DiscordBot] [UTILITY: Cleanup database messages]')
        print('Logged in as the following user:')
        print(self.user.name)
        print(self.user.id)
        print('------')

        try:
            await self.database.connect(config["database-uri"])
        except Exception:
            self.logger.error("Unable to connect to specified database!")
            traceback.print_exc()
            await self.logout()
            return

        print("working on this...")
        async with threadpool():
            with self.database.get_session() as session:
                guilds = session.query(Guilds).all()
                count = 0
                for guild in guilds:
                    count += 1
                    print("[{}] snowflake-{} name-{}".format(count, guild.guild_id, guild.name))
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
                        print("    --{} [{}]".format(channel["name"], d))
                    d = session.query(Messages).filter(Messages.guild_id == guild.guild_id, ~Messages.channel_id.in_(active_channels)).delete(synchronize_session=False)
                    session.commit()
                    print("    INACTIVE {}".format(d))
        print("done!")
        await self.logout()

def main():
    print("Starting...")
    te = Titan()
    te.run()
    gc.collect()

if __name__ == '__main__':
    main()
