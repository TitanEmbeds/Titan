class Commands():
    def __init__(self, client, database):
        self.client = client
        self.database = database

    async def ban(self, message):
        if not message.author.server_permissions.ban_members:
            await self.client.send_message(message.channel, message.author.mention + " I'm sorry, but you do not have permissions to ban guest members.")
            return
        serverid = message.server.id
        content = message.content.strip()
        if len(content.split()) == 2:
            await self.client.send_message(message.channel, message.author.mention + " Please provide a username-query (or optionally a discriminator) to ban a guest user.\nExample: `ban Titan#0001`")
            return
        content = content.split()
        username = content[2][:content[2].find("#")] if "#" in content[2] else content[2]
        discriminator = int(content[2][content[2].find("#") + 1:]) if "#" in content[2] else None
        reason = await self.database.ban_unauth_user_by_query(message.server.id, message.author.id, username, discriminator)
        await self.client.send_message(message.channel, message.author.mention + " " + reason)

    async def kick(self, message):
        if not message.author.server_permissions.kick_members:
            await self.client.send_message(message.channel, message.author.mention + " I'm sorry, but you do not have permissions to kick guest members.")
            return
        serverid = message.server.id
        content = message.content.strip()
        if len(content.split()) == 2:
            await self.client.send_message(message.channel, message.author.mention + " Please provide a username-query (or optionally a discriminator) to kick a guest user.\nExample: `kick Titan#0001`")
            return
        content = content.split()
        username = content[2][:content[2].find("#")] if "#" in content[2] else content[2]
        discriminator = int(content[2][content[2].find("#") + 1:]) if "#" in content[2] else None
        reason = await self.database.revoke_unauth_user_by_query(message.server.id, username, discriminator)
        await self.client.send_message(message.channel, message.author.mention + " " + reason)
