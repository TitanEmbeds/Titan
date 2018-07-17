import aiohttp

class DiscordBotsOrg(): # https://discordbots.org
    def __init__(self, client_id, token):
        self.url = "https://discordbots.org/api/bots/{}/stats".format(client_id)
        self.token = token

    async def post(self, count, shard_count, shard_id):
        headers = {"Authorization": self.token}
        payload = {"server_count": count, "shard_count": shard_count, "shard_no": shard_id}
        async with aiohttp.ClientSession() as aioclient:
            await aioclient.post(self.url, data=payload, headers=headers)

class BotsDiscordPw(): # https://bots.discord.pw/
    def __init__(self, client_id, token):
        self.url = "https://bots.discord.pw/api/bots/{}/stats".format(client_id)
        self.token = token

    async def post(self, count, shard_count, shard_id):
        headers = {"Authorization": self.token}
        payload = {"server_count": count, "shard_count": shard_count, "shard_id": shard_id}
        async with aiohttp.ClientSession() as aioclient:
            await aioclient.post(self.url, json=payload, headers=headers)
