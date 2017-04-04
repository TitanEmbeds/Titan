from flask import Blueprint, render_template, abort, redirect, url_for, session
from titanembeds.utils import check_guild_existance, discord_api, guild_query_unauth_users_bool
from titanembeds.oauth import generate_guild_icon_url, generate_avatar_url, check_user_can_administrate_guild
import random

embed = Blueprint("embed", __name__)

def get_logingreeting():
    greetings = [
        "Let's get to know each other! My name is Titan, what's yours?",
        "Hello and welcome!",
        "What brings you here today?",
        "....what do you expect this text to say?",
        "Aha! ..made you look!",
        "Initiating launch sequence...",
        "Captain, what's your option?",
        "Alright, here's the usual~",
    ]
    return random.choice(greetings)

@embed.route("/<string:guild_id>")
def guild_embed(guild_id):
    print guild_id
    if check_guild_existance(guild_id):
        guild = discord_api.get_guild(guild_id)['content']
        return render_template("embed.html.j2", 
            login_greeting=get_logingreeting(), 
            guild_id=guild_id, guild=guild, 
            generate_guild_icon=generate_guild_icon_url, 
            unauth_enabled=guild_query_unauth_users_bool(guild_id)
        )
    abort(404)

@embed.route("/signin_complete")
def signin_complete():
    return render_template("signin_complete.html.j2")

@embed.route("/login_discord")
def login_discord():
    return redirect(url_for("user.login_authenticated", redirect=url_for("embed.signin_complete", _external=True)))