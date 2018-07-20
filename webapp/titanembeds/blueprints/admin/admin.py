from flask import Blueprint, url_for, redirect, session, render_template, abort, request, jsonify
from flask_socketio import emit
from functools import wraps
from titanembeds.database import db, get_administrators_list, Cosmetics, Guilds, UnauthenticatedUsers, UnauthenticatedBans, TitanTokens, TokenTransactions, get_titan_token, set_titan_token, list_disabled_guilds, DisabledGuilds, UserCSS, AuthenticatedUsers, DiscordBotsOrgTransactions
from titanembeds.oauth import generate_guild_icon_url
from titanembeds.utils import get_online_embed_user_keys, redisqueue
import datetime
import json
from sqlalchemy import func
import operator

admin = Blueprint("admin", __name__)

def is_admin(f):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for("index"))
            if str(session['user_id']) not in get_administrators_list():
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator(f)

def get_online_users_count():
    users = get_online_embed_user_keys()
    auths = len(users["AuthenticatedUsers"])
    unauths = len(users["UnauthenticatedUsers"])
    return {"authenticated": auths, "guest": unauths, "total": auths + unauths}

@admin.route("/")
@is_admin
def index():
    return render_template("admin_index.html.j2", count=get_online_users_count())

@admin.route("/cosmetics", methods=["GET"])
@is_admin
def cosmetics():
    entries = db.session.query(Cosmetics).all()
    return render_template("admin_cosmetics.html.j2", cosmetics=entries)

@admin.route("/cosmetics", methods=["POST"])
@is_admin
def cosmetics_post():
    user_id = request.form.get("user_id", None)
    if not user_id:
        abort(400)
    css = request.form.get("css", None)
    css_limit = int(request.form.get("css_limit", 0))
    guest_icon = request.form.get("guest_icon", None)
    badges = request.form.get("badges", None)
    entry = db.session.query(Cosmetics).filter(Cosmetics.user_id == user_id).first()
    if entry:
        abort(409)
    user = Cosmetics(user_id)
    if css:
        css = css.lower() == "true"
        user.css = css
    if css_limit is not None:
        user.css_limit = css_limit
    if guest_icon is not None:
        guest_icon = guest_icon.lower() == "true"
        user.guest_icon = guest_icon
    if badges is not None:
        badges = badges.split(",")
        if badges == [""]:
            badges = []
        user.badges = json.dumps(badges)
    db.session.add(user)
    db.session.commit()
    return ('', 204)

@admin.route("/cosmetics", methods=["DELETE"])
@is_admin
def cosmetics_delete():
    user_id = request.form.get("user_id", None)
    if not user_id:
        abort(400)
    entry = db.session.query(Cosmetics).filter(Cosmetics.user_id == user_id).first()
    if not entry:
        abort(409)
    db.session.delete(entry)
    db.session.commit()
    return ('', 204)

@admin.route("/cosmetics", methods=["PATCH"])
@is_admin
def cosmetics_patch():
    user_id = request.form.get("user_id", None)
    if not user_id:
        abort(400)
    css = request.form.get("css", None)
    css_limit = request.form.get("css_limit", None)
    guest_icon = request.form.get("guest_icon", None)
    badges = request.form.get("badges", None)
    entry = db.session.query(Cosmetics).filter(Cosmetics.user_id == user_id).first()
    if not entry:
        abort(409)
    if css:
        css = css.lower() == "true"
        entry.css = css
    if css_limit is not None:
        entry.css_limit = css_limit
    if guest_icon:
        guest_icon = guest_icon.lower() == "true"
        entry.guest_icon = guest_icon
    if badges is not None:
        badges = badges.split(",")
        if badges == [""]:
            badges = []
        entry.badges = json.dumps(badges)
    db.session.commit()
    return ('', 204)
    
def prepare_guild_members_list(members, bans):
    all_users = []
    ip_pool = []
    members = sorted(members, key=lambda k: k.id, reverse=True)
    for member in members:
        user = {
            "id": member.id,
            "username": member.username,
            "discrim": member.discriminator,
            "ip": member.ip_address,
            "kicked": member.revoked,
            "banned": False,
            "banned_timestamp": None,
            "banned_by": None,
            "banned_reason": None,
            "ban_lifted_by": None,
            "aliases": [],
        }
        for banned in bans:
            if banned.ip_address == member.ip_address:
                if banned.lifter_id is None:
                    user['banned'] = True
                user["banned_timestamp"] = banned.timestamp
                user['banned_by'] = banned.placer_id
                user['banned_reason'] = banned.reason
                user['ban_lifted_by'] = banned.lifter_id
            continue
        if user["ip"] not in ip_pool:
            all_users.append(user)
            ip_pool.append(user["ip"])
        else:
            for usr in all_users:
                if user["ip"] == usr["ip"]:
                    alias = user["username"]+"#"+str(user["discrim"])
                    if len(usr["aliases"]) < 5 and alias not in usr["aliases"]:
                        usr["aliases"].append(alias)
                    continue
    return all_users

@admin.route("/administrate_guild/<guild_id>", methods=["GET"])
@is_admin
def administrate_guild(guild_id):
    guild = redisqueue.get_guild(guild_id)
    if not guild:
        abort(404)
        return
    db_guild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    if not db_guild:
        db_guild = Guilds(guild["id"])
        db.session.add(db_guild)
        db.session.commit()
    session["redirect"] = None
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session['user_id']).first()
    permissions=[]
    permissions.append("Manage Embed Settings")
    permissions.append("Ban Members")
    permissions.append("Kick Members")
    all_members = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id).order_by(UnauthenticatedUsers.id).all()
    all_bans = db.session.query(UnauthenticatedBans).filter(UnauthenticatedBans.guild_id == guild_id).all()
    users = prepare_guild_members_list(all_members, all_bans)
    dbguild_dict = {
        "id": guild["id"],
        "name": guild["name"],
        "unauth_users": db_guild.unauth_users,
        "visitor_view": db_guild.visitor_view,
        "webhook_messages": db_guild.webhook_messages,
        "chat_links": db_guild.chat_links,
        "bracket_links": db_guild.bracket_links,
        "mentions_limit": db_guild.mentions_limit,
        "unauth_captcha": db_guild.unauth_captcha,
        "icon": guild["icon"],
        "invite_link": db_guild.invite_link if db_guild.invite_link != None else "",
        "guest_icon": db_guild.guest_icon if db_guild.guest_icon != None else "",
        "post_timeout": db_guild.post_timeout,
        "max_message_length": db_guild.max_message_length,
        "banned_words_enabled": db_guild.banned_words_enabled,
        "banned_words_global_included": db_guild.banned_words_global_included,
        "banned_words": json.loads(db_guild.banned_words),
    }
    return render_template("administrate_guild.html.j2", guild=dbguild_dict, members=users, permissions=permissions, cosmetics=cosmetics)

@admin.route("/administrate_guild/<guild_id>", methods=["POST"])
@is_admin
def update_administrate_guild(guild_id):
    db_guild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    db_guild.unauth_users = request.form.get("unauth_users", db_guild.unauth_users) in ["true", True]
    db_guild.visitor_view = request.form.get("visitor_view", db_guild.visitor_view) in ["true", True]
    db_guild.webhook_messages = request.form.get("webhook_messages", db_guild.webhook_messages) in ["true", True]
    db_guild.chat_links = request.form.get("chat_links", db_guild.chat_links) in ["true", True]
    db_guild.bracket_links = request.form.get("bracket_links", db_guild.bracket_links) in ["true", True]
    db_guild.mentions_limit = request.form.get("mentions_limit", db_guild.mentions_limit)
    db_guild.unauth_captcha = request.form.get("unauth_captcha", db_guild.unauth_captcha) in ["true", True]
    db_guild.post_timeout = request.form.get("post_timeout", db_guild.post_timeout)
    db_guild.max_message_length = request.form.get("max_message_length", db_guild.max_message_length)
    db_guild.banned_words_enabled = request.form.get("banned_words_enabled", db_guild.banned_words_enabled) in ["true", True]
    db_guild.banned_words_global_included = request.form.get("banned_words_global_included", db_guild.banned_words_global_included) in ["true", True]
    invite_link = request.form.get("invite_link", db_guild.invite_link)
    if invite_link != None and invite_link.strip() == "":
        invite_link = None
    db_guild.invite_link = invite_link
    guest_icon = request.form.get("guest_icon", db_guild.guest_icon)
    if guest_icon != None and guest_icon.strip() == "":
        guest_icon = None
    db_guild.guest_icon = guest_icon
    banned_word = request.form.get("banned_word", None)
    if banned_word:
        delete_banned_word = request.form.get("delete_banned_word", False) in ["true", True]
        banned_words = set(json.loads(db_guild.banned_words))
        if delete_banned_word:
            banned_words.discard(banned_word)
        else:
            banned_words.add(banned_word)
        db_guild.banned_words = json.dumps(list(banned_words))
    db.session.commit()
    emit("guest_icon_change", {"guest_icon": guest_icon if guest_icon else url_for('static', filename='img/titanembeds_square.png')}, room="GUILD_"+guild_id, namespace="/gateway")
    return jsonify(
        guild_id=db_guild.guild_id,
        unauth_users=db_guild.unauth_users,
        visitor_view=db_guild.visitor_view,
        webhook_messages=db_guild.webhook_messages,
        chat_links=db_guild.chat_links,
        bracket_links=db_guild.bracket_links,
        mentions_limit=db_guild.mentions_limit,
        invite_link=db_guild.invite_link,
        guest_icon=db_guild.guest_icon,
        unauth_captcha=db_guild.unauth_captcha,
        post_timeout=db_guild.post_timeout,
        max_message_length=db_guild.max_message_length,
        banned_words_enabled=db_guild.banned_words_enabled,
        banned_words_global_included=db_guild.banned_words_global_included,
        banned_words=json.loads(db_guild.banned_words),
    )

@admin.route("/guilds")
@is_admin
def guilds():
    guilds = db.session.query(Guilds).all()
    return render_template("admin_guilds.html.j2", servers=guilds, icon_generate=generate_guild_icon_url)

@admin.route("/tokens", methods=["GET"])
@is_admin
def manage_titan_tokens():
    tokeners = db.session.query(TitanTokens).all()
    donators = []
    for usr in tokeners:
        row = {
            "user_id": usr.user_id,
            "tokens": usr.tokens,
            "transactions": []
        }
        transact = db.session.query(TokenTransactions).filter(TokenTransactions.user_id == usr.user_id).all()
        for tr in transact:
            row["transactions"].append({
                "id": tr.id,
                "user_id": tr.user_id,
                "timestamp": tr.timestamp,
                "action": tr.action,
                "net_tokens": tr.net_tokens,
                "start_tokens": tr.start_tokens,
                "end_tokens": tr.end_tokens
            })
        donators.append(row)
    return render_template("admin_token_transactions.html.j2", donators=donators)

@admin.route("/tokens", methods=["POST"])
@is_admin
def post_titan_tokens():
    user_id = request.form.get("user_id", None)
    amount = request.form.get("amount", None, type=int)
    reason = request.form.get("reason", None)
    if not user_id or not amount:
        abort(400)
    if get_titan_token(user_id) != -1:
        abort(409)
    set_titan_token(user_id, amount, "NEW VIA ADMIN [{}]".format(str(reason)))
    db.session.commit()
    return ('', 204)

@admin.route("/tokens", methods=["PATCH"])
@is_admin
def patch_titan_tokens():
    user_id = request.form.get("user_id", None)
    amount = request.form.get("amount", None, type=int)
    reason = request.form.get("reason", None)
    if not user_id or not amount:
        abort(400)
    if get_titan_token(user_id) == -1:
        abort(409)
    set_titan_token(user_id, amount, "MODIFY VIA ADMIN [{}]".format(str(reason)))
    db.session.commit()
    return ('', 204)

@admin.route("/disabled_guilds", methods=["GET"])
@is_admin
def get_disabled_guilds():
    return render_template("admin_disabled_guilds.html.j2", guilds=list_disabled_guilds())

@admin.route("/disabled_guilds", methods=["POST"])
@is_admin
def post_disabled_guilds():
    guild_id = request.form.get("guild_id", None)
    if guild_id in list_disabled_guilds():
        abort(409)
    guild = DisabledGuilds(guild_id)
    db.session.add(guild)
    db.session.commit()
    return ('', 204)

@admin.route("/disabled_guilds", methods=["DELETE"])
@is_admin
def delete_disabled_guilds():
    guild_id = request.form.get("guild_id", None)
    if guild_id not in list_disabled_guilds():
        abort(409)
    guild = db.session.query(DisabledGuilds).filter(DisabledGuilds.guild_id == guild_id).first()
    db.session.delete(guild)
    db.session.commit()
    return ('', 204)

@admin.route("/custom_css", methods=["GET"])
@is_admin
def list_custom_css_get():
    css = db.session.query(UserCSS).order_by(UserCSS.id).all()
    return render_template("admin_usercss.html.j2", css=css)

@admin.route("/custom_css/edit/<css_id>", methods=["GET"])
@is_admin
def edit_custom_css_get(css_id):
    css = db.session.query(UserCSS).filter(UserCSS.id == css_id).first()
    if not css:
        abort(404)
    variables = css.css_variables
    if variables:
        variables = json.loads(variables)
    return render_template("usercss.html.j2", new=False, css=css, variables=variables, admin=True)

@admin.route("/custom_css/edit/<css_id>", methods=["POST"])
@is_admin
def edit_custom_css_post(css_id):
    dbcss = db.session.query(UserCSS).filter(UserCSS.id == css_id).first()
    if not dbcss:
        abort(404)
    name = request.form.get("name", None)
    user_id = request.form.get("user_id", None)
    css = request.form.get("css", None)
    variables = request.form.get("variables", None)
    variables_enabled = request.form.get("variables_enabled", False) in ["true", True]
    if not name:
        abort(400)
    else:
        name = name.strip()
        css = css.strip()
    if not user_id:
        user_id = dbcss.user_id
    if (len(css) == 0):
        css = None
    dbcss.name = name
    dbcss.user_id = user_id
    dbcss.css = css
    dbcss.css_variables = variables
    dbcss.css_var_bool = variables_enabled
    db.session.commit()
    return jsonify({"id": dbcss.id})
    
@admin.route("/custom_css/edit/<css_id>", methods=["DELETE"])
@is_admin
def edit_custom_css_delete(css_id):
    dbcss = db.session.query(UserCSS).filter(UserCSS.id == css_id).first()
    if not dbcss:
        abort(404)
    db.session.delete(dbcss)
    db.session.commit()
    return jsonify({})

@admin.route("/custom_css/new", methods=["GET"])
@is_admin
def new_custom_css_get():
    return render_template("usercss.html.j2", new=True, admin=True)
    
@admin.route("/custom_css/new", methods=["POST"])
@is_admin
def new_custom_css_post():
    name = request.form.get("name", None)
    user_id = request.form.get("user_id", None)
    css = request.form.get("css", None)
    variables = request.form.get("variables", None)
    variables_enabled = request.form.get("variables_enabled", False) in ["true", True]
    if not name:
        abort(400)
    else:
        name = name.strip()
        css = css.strip()
    if not user_id:
        abort(400)
    if (len(css) == 0):
        css = None
    css = UserCSS(name, user_id, variables_enabled, variables, css)
    db.session.add(css)
    db.session.commit()
    return jsonify({"id": css.id})

@admin.route("/voting", methods=["GET"])
@is_admin
def voting_get():
    datestart = request.args.get("datestart")
    timestart = request.args.get("timestart")
    dateend = request.args.get("dateend")
    timeend = request.args.get("timeend")
    if not datestart or not timestart or not dateend or not timeend:
        return render_template("admin_voting.html.j2")
    start = datetime.datetime.strptime(datestart + " " + timestart, '%d %B, %Y %I:%M%p')
    end = datetime.datetime.strptime(dateend + " " + timeend, '%d %B, %Y %I:%M%p')
    users = db.session.query(DiscordBotsOrgTransactions).filter(DiscordBotsOrgTransactions.timestamp >= start, DiscordBotsOrgTransactions.timestamp <= end).order_by(DiscordBotsOrgTransactions.timestamp)
    all_users = []
    for u in users:
        uid = u.user_id # Let's fix this OBO error
        gmember = db.session.query(GuildMembers).filter(GuildMembers.user_id == uid).first()
        count = 0
        if not gmember:
            uid = uid - 10
            while uid < u.user_id + 10:
                gmember = db.session.query(GuildMembers).filter(GuildMembers.user_id == uid).first()
                if gmember:
                    break
                uid = uid + 1
        all_users.append({
            "id": u.id,
            "user_id": uid,
            "timestamp": u.timestamp,
            "action": u.action,
            "referrer": u.referrer
        })
    overall_votes = {}
    for u in all_users:
        uid = u["user_id"]
        action = u["action"]
        if uid not in overall_votes:
            overall_votes[uid] = 0
        if action == "none":
            overall_votes[uid] = overall_votes[uid] - 1
        if action == "upvote":
            overall_votes[uid] = overall_votes[uid] + 1
    sorted_overall_votes = []
    for uid, votes in sorted(overall_votes.items(), key=operator.itemgetter(1), reverse=True):
        sorted_overall_votes.append(uid)
    overall = []
    for uid in sorted_overall_votes:
        gmember = db.session.query(GuildMembers).filter(GuildMembers.user_id == uid).first()
        u = {
            "user_id": uid,
            "votes": overall_votes[uid]
        }
        if gmember:
            u["discord"] = gmember.username + "#" + str(gmember.discriminator)
        overall.append(u)
    referrer = {}
    for u in all_users:
        if not u["referrer"] or u["referrer"] == u["user_id"]:
            continue
        refer = u["referrer"]
        if refer not in referrer:
            referrer[refer] = 0
        referrer[refer] = referrer[refer] + 1
    sorted_referrers = []
    for uid, votes in sorted(referrer.items(), key=operator.itemgetter(1), reverse=True):
        sorted_referrers.append(uid)
    referrals = []
    for uid in sorted_referrers:
        gmember = db.session.query(GuildMembers).filter(GuildMembers.user_id == uid).first()
        u = {
            "user_id": uid,
            "votes": referrer[uid]
        }
        if gmember:
            u["discord"] = gmember.username + "#" + str(gmember.discriminator)
        referrals.append(u)
    return render_template("admin_voting.html.j2", overall=overall, referrals=referrals, datestart=datestart, timestart=timestart, dateend=dateend, timeend=timeend)