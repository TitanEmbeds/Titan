class Commands():
    def __init__(self, client, database):
        self.client = client
        self.database = database
    
    async def ban(self, message):
        pass
        #await self.client.send_message(message.channel, "test test!")