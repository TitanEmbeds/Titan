class Commands():
    def __init__(self, client, database):
        self.client = client
        self.database = database

    async def ban(self, message):
        if not message.author.guild_permissions.ban_members:
            await message.channel.send(message.author.mention + " I'm sorry, but you do not have permissions to ban guest members.")
            return
        serverid = message.guild.id
        content = message.content.strip()
        if len(content.split()) == 2:
            await message.channel.send(message.author.mention + " Please provide a username-query (or optionally a discriminator) to ban a guest user.\nExample: `ban Titan#0001`")
            return
        content = content.split()
        username = content[2][:content[2].find("#")] if "#" in content[2] else content[2]
        discriminator = int(content[2][content[2].find("#") + 1:]) if "#" in content[2] else None
        reason = await self.database.ban_unauth_user_by_query(message.guild.id, message.author.id, username, discriminator)
        await message.channel.send(message.author.mention + " " + reason)

    async def kick(self, message):
        if not message.author.guild_permissions.kick_members:
            await message.channel.send(message.author.mention + " I'm sorry, but you do not have permissions to kick guest members.")
            return
        serverid = message.guild.id
        content = message.content.strip()
        if len(content.split()) == 2:
            await message.channel.send(message.author.mention + " Please provide a username-query (or optionally a discriminator) to kick a guest user.\nExample: `kick Titan#0001`")
            return
        content = content.split()
        username = content[2][:content[2].find("#")] if "#" in content[2] else content[2]
        discriminator = int(content[2][content[2].find("#") + 1:]) if "#" in content[2] else None
        reason = await self.database.revoke_unauth_user_by_query(message.guild.id, username, discriminator)
        await message.channel.send(message.author.mention + " " + reason)

    async def invite(self, message):
        await message.channel.send("You can invite Titan to your server by visiting this link: https://discordapp.com/oauth2/authorize?&client_id=299403260031139840&scope=bot&permissions=641195117")
        
    async def server(self, message):
        await message.channel.send("Join the Titan Embeds Discord server! https://discord.gg/pFDDtcN")
        
    async def shard(self, message):
        await message.channel.send("This instance of Titan Embeds Discord Bot is running on shard **{}**. There are **{}** shards in total.".format(self.client.shard_id, self.client.shard_count))