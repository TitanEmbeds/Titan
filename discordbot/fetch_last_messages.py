from config import config
from titanembeds.database import DatabaseInterface
from titanembeds.commands import Commands
import discord
import aiohttp
import asyncio
import sys
import logging
import gc
logging.basicConfig(filename='titanbot.log',level=logging.INFO,format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.getLogger('TitanBot')
logging.getLogger('sqlalchemy')

###########################
#   Fetch Last Messages   #
#                         #
# Fills the database with #
# the last 50 messages of #
# each channel.           #
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
        print('Titan [DiscordBot] [UTILITY: Fetch last messages]')
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
        all_channels = []
        if len(sys.argv) < 2:
            print("fetch_last_messages.py <server/all> [server_id]")
            await self.logout()
            return
        if "server" == sys.argv[1]:
            server_id = sys.argv[2]
            server = self.get_guild(server_id)
            if not server:
                print("Server not found")
                await self.logout()
                return
            print("Getting server: " + str(server))
            all_channels = server.channels
        elif "all" == sys.argv[1]:
            print("Getting all channels")
            all_channels = list(self.get_all_channels())
        else:
            print("fetch_last_messages.py <server/all> [server_id]")
            await self.logout()
            return
        for channel in all_channels:
            try:
                if str(channel.type) == "text":
                    print("Processing channel: ID-{} Name-'{}' ServerID-{} Server-'{}'".format(channel.id, channel.name, channel.guild.id, channel.guild.name))
                    await self.database.delete_all_messages_from_channel(channel.id)
                    async for message in self.logs_from(channel, limit=50, reverse=True):
                        await self.database.push_message(message)
            except:
                continue
        print("done!")
        await self.logout()

def main():
    print("Starting...")
    te = Titan()
    te.run()
    gc.collect()

if __name__ == '__main__':
    main()
