import aiohttp

class Commands():
    def __init__(self, client, config):
        self.client = client
        self.config = config

    async def ban(self, message):
        if not message.author.guild_permissions.ban_members:
            await message.channel.send(message.author.mention + " I'm sorry, but you do not have permissions to ban guest members.")
            return
        content = message.content.strip()
        if len(content.split()) == 2:
            await message.channel.send(message.author.mention + " Please provide a username-query (or optionally a discriminator) to ban a guest user.\nExample: `ban Titan#0001`")
            return
        content = content.split()
        username = content[2][:content[2].find("#")] if "#" in content[2] else content[2]
        discriminator = int(content[2][content[2].find("#") + 1:]) if "#" in content[2] else None
        headers = {"Authorization": self.config["bot-token"]}
        payload = {
            "guild_id": message.guild.id,
            "placer_id": message.author.id,
            "username": username
        }
        if discriminator:
            payload["discriminator"] = discriminator
        url = self.config["titan-web-url"] + "api/bot/ban"
        async with aiohttp.ClientSession() as aioclient:
            async with aioclient.post(url, json=payload, headers=headers) as resp:
                j = await resp.json()
                if "error" in j:
                    await message.channel.send(message.author.mention + " Ban error! " + j["error"])
                    return
                if "success" in j:
                    await message.channel.send(message.author.mention + " " + j["success"])
                    return
        await message.channel.send("Unhandled webservice error in banning guest user!")

    async def kick(self, message):
        if not message.author.guild_permissions.kick_members:
            await message.channel.send(message.author.mention + " I'm sorry, but you do not have permissions to kick guest members.")
            return
        content = message.content.strip()
        if len(content.split()) == 2:
            await message.channel.send(message.author.mention + " Please provide a username-query (or optionally a discriminator) to kick a guest user.\nExample: `kick Titan#0001`")
            return
        content = content.split()
        username = content[2][:content[2].find("#")] if "#" in content[2] else content[2]
        discriminator = int(content[2][content[2].find("#") + 1:]) if "#" in content[2] else None
        headers = {"Authorization": self.config["bot-token"]}
        payload = {
            "guild_id": message.guild.id,
            "username": username
        }
        if discriminator:
            payload["discriminator"] = discriminator
        url = self.config["titan-web-url"] + "api/bot/revoke"
        async with aiohttp.ClientSession() as aioclient:
            async with aioclient.post(url, json=payload, headers=headers) as resp:
                j = await resp.json()
                if "error" in j:
                    await message.channel.send(message.author.mention + " Kick error! " + j["error"])
                    return
                if "success" in j:
                    await message.channel.send(message.author.mention + " " + j["success"])
                    return
        await message.channel.send("Unhandled webservice error in kicking guest user!")

    async def invite(self, message):
        await message.channel.send("You can invite Titan to your server by visiting this link: https://discordapp.com/oauth2/authorize?&client_id=299403260031139840&scope=bot&permissions=641195117")
        
    async def server(self, message):
        await message.channel.send("Join the Titan Embeds Discord server! https://discord.gg/pFDDtcN")
        
    async def shard(self, message):
        await message.channel.send("This instance of Titan Embeds Discord Bot is running on shard **{}**. There are **{}** shards in total.".format(message.guild.shard_id, self.client.shard_count))