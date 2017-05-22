from flask import Blueprint, render_template, abort, redirect, url_for, session, request
from titanembeds.utils import check_guild_existance, guild_query_unauth_users_bool
from titanembeds.oauth import generate_guild_icon_url, generate_avatar_url
from titanembeds.database import db, Guilds, UserCSS
from config import config
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

def get_custom_css():
    css = request.args.get("css", None)
    if css:
        css = db.session.query(UserCSS).filter(UserCSS.id == css).first()
    return css

@embed.route("/<string:guild_id>")
def guild_embed(guild_id):
    if check_guild_existance(guild_id):
        guild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
        guild_dict = {
            "id": guild.guild_id,
            "name": guild.name,
            "unauth_users": guild.unauth_users,
            "icon": guild.icon
        }
        return render_template("embed.html.j2",
            login_greeting=get_logingreeting(),
            guild_id=guild_id, guild=guild_dict,
            generate_guild_icon=generate_guild_icon_url,
            unauth_enabled=guild_query_unauth_users_bool(guild_id),
            client_id=config['client-id'],
            css=get_custom_css()
        )
    abort(404)

@embed.route("/signin_complete")
def signin_complete():
    return render_template("signin_complete.html.j2")

@embed.route("/login_discord")
def login_discord():
    return redirect(url_for("user.login_authenticated", redirect=url_for("embed.signin_complete", _external=True)))
