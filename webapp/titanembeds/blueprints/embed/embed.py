from flask import Blueprint, render_template, abort, redirect, url_for, session, request
from flask_babel import gettext
from titanembeds.utils import check_guild_existance, guild_query_unauth_users_bool, guild_accepts_visitors, guild_unauthcaptcha_enabled
from titanembeds.oauth import generate_guild_icon_url, generate_avatar_url
from titanembeds.database import db, Guilds, UserCSS, list_disabled_guilds
from config import config
import random
import json
from urllib.parse import urlparse

embed = Blueprint("embed", __name__)

def get_logingreeting():
    greetings = [
        gettext("Let's get to know each other! My name is Titan, what's yours?"),
        gettext("Hello and welcome!"),
        gettext("What brings you here today?"),
        gettext("....what do you expect this text to say?"),
        gettext("Aha! ..made you look!"),
        gettext("Initiating launch sequence..."),
        gettext("Captain, what's your option?"),
        gettext("Alright, here's the usual~"),
    ]
    return random.choice(greetings)

def get_custom_css():
    css = request.args.get("css", None)
    if css:
        css = db.session.query(UserCSS).filter(UserCSS.id == css).first()
    return css

def parse_css_variable(css):
    CSS_VARIABLES_TEMPLATE = """:root {
      /*--<var>: <value>*/
      --modal: %(modal)s;
      --noroleusers: %(noroleusers)s;
      --main: %(main)s;
      --placeholder: %(placeholder)s;
      --sidebardivider: %(sidebardivider)s;
      --leftsidebar: %(leftsidebar)s;
      --rightsidebar: %(rightsidebar)s;
      --header: %(header)s;
      --chatmessage: %(chatmessage)s;
      --discrim: %(discrim)s;
      --chatbox: %(chatbox)s;
    }"""
    if not css:
        return None
    else:
        variables = css.css_variables
        if variables:
            variables = json.loads(variables)
            return CSS_VARIABLES_TEMPLATE % variables
    return None

def parse_url_domain(url):
    parsed = urlparse(url)
    if parsed.netloc != "":
        return parsed.netloc
    return url

@embed.route("/<string:guild_id>")
def guild_embed(guild_id):
    if check_guild_existance(guild_id):
        guild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
        guild_dict = {
            "id": guild.guild_id,
            "name": guild.name,
            "unauth_users": guild.unauth_users,
            "icon": guild.icon,
            "invite_link": guild.invite_link,
            "invite_domain": parse_url_domain(guild.invite_link),
        }
        customcss = get_custom_css()
        return render_template("embed.html.j2",
            disabled=guild_id in list_disabled_guilds(),
            login_greeting=get_logingreeting(),
            guild_id=guild_id,
            guild=guild_dict,
            generate_guild_icon=generate_guild_icon_url,
            unauth_enabled=guild_query_unauth_users_bool(guild_id),
            visitors_enabled=guild_accepts_visitors(guild_id),
            unauth_captcha_enabled=guild_unauthcaptcha_enabled(guild_id),
            client_id=config['client-id'],
            recaptcha_site_key=config["recaptcha-site-key"],
            css=customcss,
            cssvariables=parse_css_variable(customcss),
            same_target=request.args.get("sametarget", False) == "true"
        )
    abort(404)

@embed.route("/signin_complete")
def signin_complete():
    return render_template("signin_complete.html.j2")

@embed.route("/login_discord")
def login_discord():
    return redirect(url_for("user.login_authenticated", redirect=url_for("embed.signin_complete", _external=True)))

@embed.route("/noscript")
def noscript():
    return render_template("noscript.html.j2")