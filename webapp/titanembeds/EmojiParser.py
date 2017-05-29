from titanembeds.utils import discord_api
import re

def parseEmoji(textToParse, guild_id):
    _endpoint = "/guilds/{guild_id}".format(guild_id=guild_id)
    _method = "GET"
    response = discord_api.request(_method, _endpoint)
    if response['content']['code'] is None:
        return textToParse
    emojis = []
    emojis = re.findall("<:(.*?):(.*)?>", textToParse)
    newText = textToParse
    for emoji in response['emojis']:
    	name = emoji['name']
    	emojiId = emoji['id']
    	for emoji2 in emojis:
    		if name.lower is emoji2.replace(":", "").lower():
    			newText = newText.replace("<:{}}:{}>".format(name, emojiId), "<img src='https://cdn.discordapp.com/emojis/{}.png'></img>".format(emojiId))
    return newText
