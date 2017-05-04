from config import config
import discord

client = discord.Client()

@client.event
async def on_ready():
    print('Titan -- DiscordBot')
    print('Logged in as the following user:')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await test()

async def test():
    from titanembeds.database import db, Guilds, session
    session.query(Guilds).all()