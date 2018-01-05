import aiohttp

class DiscordBotsOrg(): # https://discordbots.org
    def __init__(self, client_id, token):
        self.url = "https://discordbots.org/api/bots/{}/stats".format(client_id)
        self.token = token
    
    async def post(self, count):
        headers = {"Authorization": self.token}
        payload = {"server_count": count}
        async with aiohttp.ClientSession() as aioclient:
            await aioclient.post(self.url, data=payload, headers=headers)