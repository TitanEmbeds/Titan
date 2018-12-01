import aiohttp
import discord

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
        headers = {"Authorization": self.config["titan-web-app-secret"]}
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
        headers = {"Authorization": self.config["titan-web-app-secret"]}
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

        async def help(self, message):
            await message.channel.send("Commands available on: https://titanembeds.com/about\nTo setup an embed please visit: https://titanembeds.com/user/dashboard")

    async def members(self, message):
        headers = {"Authorization": self.config["titan-web-app-secret"]}
        payload = {
            "guild_id": message.guild.id,
        }
        users = {"authenticated": [], "unauthenticated": []}
        url = self.config["titan-web-url"] + "api/bot/members"
        async with aiohttp.ClientSession() as aioclient:
            async with aioclient.get(url, params=payload, headers=headers) as resp:
                if resp.status >= 200 and resp.status < 300:
                    users = await resp.json()
        embed_description = ""
        if users["authenticated"]:
            embed_description = embed_description + "__(Discord)__\n"
            count = 1
            for user in users["authenticated"]:
                server_user = message.guild.get_member(int(user["id"]))
                embed_description = embed_description + "**{}.** {}#{}".format(count, server_user.name, server_user.discriminator)
                if server_user.nick:
                    embed_description = embed_description + " ({})".format(server_user.nick)
                embed_description = embed_description + " {}\n".format(server_user.mention)
                count = count + 1
        if users["unauthenticated"]:
            if users["authenticated"]:
                embed_description = embed_description + "\n"
            embed_description = embed_description + "__(Guest)__\n"
            count = 1
            for user in users["unauthenticated"]:
                embed_description = embed_description + "**{}.** {}#{}\n".format(count, user["username"], user["discriminator"])
                count = count + 1
        if users["authenticated"] or users["unauthenticated"]:
            embed_description = embed_description + "\n"
        embed_description = embed_description + "**Total Members Online: __{}__**".format(len(users["authenticated"]) + len(users["unauthenticated"]))
        embed = discord.Embed(
            title = "Currently Online Embed Members",
            url = "https://TitanEmbeds.com/",
            color = 7964363,
            description = embed_description
        )
        if message.guild.me.permissions_in(message.channel).embed_links:
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("__**Currently Online Embed Members**__\n" + embed_description)
