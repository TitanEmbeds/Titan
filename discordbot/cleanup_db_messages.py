from config import config
from titanembeds.database import DatabaseInterface, Guilds, Messages
from titanembeds.commands import Commands
import discord
import aiohttp
import asyncio
import sys
import logging
import json
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
            await self.database.connect(config["database-uri"] + "?charset=utf8mb4")
        except Exception:
            self.logger.error("Unable to connect to specified database!")
            traceback.print_exc()
            await self.logout()
            return

        print("working on this...")
        async with threadpool():
            with self.database.get_session() as session:
                guilds = session.query(Guilds).all()
                for guild in guilds:
                    print("id-{} snowflake-{} name-{}".format(guild.id, guild.guild_id, guild.name))
                    try:
                        channelsjson = json.loads(guild.channels)
                    except:
                        continue
                    for channel in channelsjson:
                        chanid = channel["id"]
                        msgs = session.query(Messages).filter(Messages.channel_id == chanid).order_by(Messages.timestamp.desc()).offset(50).all()
                        for msg in msgs:
                            session.delete(msg)
                    session.commit()
        print("done!")
        await self.logout()

def main():
    print("Starting...")
    te = Titan()
    te.run()
    gc.collect()

if __name__ == '__main__':
    main()