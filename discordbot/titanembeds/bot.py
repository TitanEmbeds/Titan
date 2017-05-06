from config import config
from titanembeds.database import DatabaseInterface
import discord
import aiohttp
import asyncio

class Titan(discord.Client):
    def __init__(self):
        super().__init__()
        self.aiosession = aiohttp.ClientSession(loop=self.loop)
        self.http.user_agent += ' TitanEmbeds-Bot'
        self.database = DatabaseInterface(self)

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
        print('Titan [DiscordBot]')
        print('Logged in as the following user:')
        print(self.user.name)
        print(self.user.id)
        print('------')

        await self.change_presence(
            game=discord.Game(name="Get your own @ https://TitanEmbeds.tk/"), status=discord.Status.online
        )

        try:
            await self.database.connect(config["database-uri"])
        except Exception:
            self.logger.error("Unable to connect to specified database!")
            traceback.print_exc()
            await self.logout()
            return

    async def on_message(self, message):
        await self.database.push_message(message)
        # TODO: Will add command handler + ban/kick command

    async def on_message_edit(self, message_before, message_after):
        await self.database.update_message(message_after)
