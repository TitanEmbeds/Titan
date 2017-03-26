from flask import Blueprint

embed = Blueprint("embed", __name__)

@embed.route("/<guild_id>")
def guild_embed(guild_id):
    return guild_id
