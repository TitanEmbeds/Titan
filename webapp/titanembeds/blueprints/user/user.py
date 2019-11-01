from flask import Blueprint, request, redirect, jsonify, abort, session, url_for, render_template
from flask import current_app as app
from flask_socketio import emit
from config import config
from titanembeds.decorators import discord_users_only
from titanembeds.database import db, Guilds, UnauthenticatedUsers, UnauthenticatedBans, Cosmetics, UserCSS, Patreon, set_titan_token, get_titan_token, add_badge, list_disabled_guilds
from titanembeds.oauth import authorize_url, token_url, make_authenticated_session, get_current_authenticated_user, get_user_managed_servers, check_user_can_administrate_guild, check_user_permission, generate_avatar_url, generate_guild_icon_url, generate_bot_invite_url
from titanembeds.utils import redisqueue
import time
import datetime
import paypalrestsdk
import json
import patreon

user = Blueprint("user", __name__)

@user.route("/login_authenticated", methods=["GET"])
def login_authenticated():
    session["redirect"] = request.args.get("redirect")
    scope = ['identify', 'guilds', 'guilds.join']
    discord = make_authenticated_session(scope=scope)
    authorization_url, state = discord.authorization_url(
        authorize_url,
        access_type="offline",
        prompt="none",
    )
    session['oauth2_state'] = state
    return redirect(authorization_url)

@user.route('/callback', methods=["GET"])
def callback():
    state = session.get('oauth2_state')
    if not state or request.values.get('error'):
        return redirect(url_for('user.logout'))
    discord = make_authenticated_session(state=state)
    discord_token = discord.fetch_token(
        token_url,
        client_secret=config['client-secret'],
        authorization_response=request.url)
    if not discord_token:
        return redirect(url_for('user.logout'))
    session['user_keys'] = discord_token
    session['unauthenticated'] = False
    session.permanent = True
    user = get_current_authenticated_user()
    session['user_id'] = int(user['id'])
    session['username'] = user['username']
    session['discriminator'] = user['discriminator']
    session['avatar'] = generate_avatar_url(user['id'], user['avatar'], user['discriminator'])
    session["tokens"] = get_titan_token(session["user_id"])
    if session["tokens"] == -1:
        session["tokens"] = 0
    if session["redirect"]:
        redir = session["redirect"]
        session['redirect'] = None
        return redirect(redir)
    return redirect(url_for("user.dashboard"))

@user.route('/logout', methods=["GET"])
def logout():
    redir = session.get("redirect", None)
    if not redir:
        redir = request.args.get("redirect", None)
    session.clear()
    if redir:
        session['redirect'] = redir
        return redirect(session['redirect'])
    return redirect(url_for("index"))

def count_user_premium_css():
    count = 0
    css_list = db.session.query(UserCSS).filter(UserCSS.user_id == session['user_id']).all()
    for css in css_list:
        if css.css is not None:
            count += 1
    return count

@user.route("/dashboard")
@discord_users_only()
def dashboard():
    guilds = get_user_managed_servers()
    error = request.args.get("error")
    if session["redirect"] and not (error and error == "access_denied"):
        redir = session['redirect']
        session['redirect'] = None
        return redirect(redir)
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session['user_id']).first()
    css_list = None
    if cosmetics and cosmetics.css:
        css_list = db.session.query(UserCSS).filter(UserCSS.user_id == session['user_id']).order_by(UserCSS.id).all()
    premium_css_count = count_user_premium_css()
    return render_template("dashboard.html.j2", servers=guilds, icon_generate=generate_guild_icon_url, cosmetics=cosmetics, css_list=css_list, premium_css_count=premium_css_count)

@user.route("/custom_css/new", methods=["GET"])
@discord_users_only()
def new_custom_css_get():
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session['user_id']).first()
    if not cosmetics or not cosmetics.css:
        abort(403)
    premium_css_count = count_user_premium_css()
    return render_template("usercss.html.j2", new=True, cosmetics=cosmetics, premium_css_count=premium_css_count)

@user.route("/custom_css/new", methods=["POST"])
@discord_users_only()
def new_custom_css_post():
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session['user_id']).first()
    if not cosmetics or not cosmetics.css:
        abort(403)
    
    name = request.form.get("name", None)
    user_id = session["user_id"]
    css = request.form.get("css",None)
    variables = request.form.get("variables", None)
    variables_enabled = request.form.get("variables_enabled", False) in ["true", True]
    if not name:
        abort(400)
    else:
        name = name.strip()
        css = css.strip()
    if (len(css) == 0):
        css = None
    css = UserCSS(name, user_id, variables_enabled, variables, css)
    db.session.add(css)
    db.session.commit()
    return jsonify({"id": css.id})

@user.route("/custom_css/edit/<css_id>", methods=["GET"])
@discord_users_only()
def edit_custom_css_get(css_id):
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session['user_id']).first()
    if not cosmetics or not cosmetics.css:
        abort(403)
    css = db.session.query(UserCSS).filter(UserCSS.id == css_id).first()
    if not css:
        abort(404)
    if str(css.user_id) != str(session['user_id']):
        abort(403)
    variables = css.css_variables
    if variables:
        variables = json.loads(variables)
    premium_css_count = count_user_premium_css()
    return render_template("usercss.html.j2", new=False, css=css, variables=variables, cosmetics=cosmetics, premium_css_count=premium_css_count)

@user.route("/custom_css/edit/<css_id>", methods=["POST"])
@discord_users_only()
def edit_custom_css_post(css_id):
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session['user_id']).first()
    if not cosmetics or not cosmetics.css:
        abort(403)
    dbcss = db.session.query(UserCSS).filter(UserCSS.id == css_id).first()
    if not dbcss:
        abort(404)
    if dbcss.user_id != session['user_id']:
        abort(403)
    name = request.form.get("name", None)
    css = request.form.get("css", None)
    variables = request.form.get("variables", None)
    variables_enabled = request.form.get("variables_enabled", False) in ["true", True]
    if not name:
        abort(400)
    else:
        name = name.strip()
        css = css.strip()
    if (len(css) == 0):
        css = None
    dbcss.name = name
    dbcss.css = css
    dbcss.css_variables = variables
    dbcss.css_var_bool = variables_enabled
    db.session.commit()
    return jsonify({"id": dbcss.id})

@user.route("/custom_css/edit/<css_id>", methods=["DELETE"])
@discord_users_only()
def edit_custom_css_delete(css_id):
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session['user_id']).first()
    if not cosmetics or not cosmetics.css:
        abort(403)
    dbcss = db.session.query(UserCSS).filter(UserCSS.id == css_id).first()
    if not dbcss:
        abort(404)
    if dbcss.user_id != session['user_id']:
        abort(403)
    db.session.delete(dbcss)
    db.session.commit()
    return jsonify({})

@user.route("/administrate_guild/<guild_id>", methods=["GET"])
@discord_users_only()
def administrate_guild(guild_id):
    if not check_user_can_administrate_guild(guild_id):
        return redirect(url_for("user.dashboard"))
    guild = redisqueue.get_guild(guild_id)
    if not guild:
        session["redirect"] = url_for("user.administrate_guild", guild_id=guild_id, _external=True)
        return redirect(url_for("user.add_bot", guild_id=guild_id))
    session["redirect"] = None
    db_guild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    if not db_guild:
        db_guild = Guilds(guild["id"])
        db.session.add(db_guild)
        db.session.commit()
    permissions=[]
    if check_user_permission(guild_id, 5):
        permissions.append("Manage Embed Settings")
    if check_user_permission(guild_id, 2):
        permissions.append("Ban Members")
    if check_user_permission(guild_id, 1):
        permissions.append("Kick Members")
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session['user_id']).first()
    all_members = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id).order_by(UnauthenticatedUsers.id).limit(2000).all()
    all_bans = db.session.query(UnauthenticatedBans).filter(UnauthenticatedBans.guild_id == guild_id).all()
    users = prepare_guild_members_list(all_members, all_bans)
    dbguild_dict = {
        "id": db_guild.guild_id,
        "name": guild["name"],
        "roles": guild["roles"],
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
        "autorole_unauth": db_guild.autorole_unauth,
        "autorole_discord": db_guild.autorole_discord,
        "file_upload": db_guild.file_upload,
    }
    return render_template("administrate_guild.html.j2", guild=dbguild_dict, members=users, permissions=permissions, cosmetics=cosmetics, disabled=(guild_id in list_disabled_guilds()))

@user.route("/administrate_guild/<guild_id>", methods=["POST"])
@discord_users_only()
def update_administrate_guild(guild_id):
    if guild_id in list_disabled_guilds():
        return ('', 423)
    if not check_user_can_administrate_guild(guild_id):
        abort(403)
    db_guild = db.session.query(Guilds).filter(Guilds.guild_id == guild_id).first()
    if not db_guild:
        abort(400)
    if not check_user_permission(guild_id, 5):
        abort(403)
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
    db_guild.autorole_unauth = request.form.get("autorole_unauth", db_guild.autorole_unauth, type=int)
    db_guild.autorole_discord = request.form.get("autorole_discord", db_guild.autorole_discord, type=int)
    db_guild.file_upload = request.form.get("file_upload", db_guild.file_upload) in ["true", True]
    
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
        guest_icon=guest_icon,
        unauth_captcha=db_guild.unauth_captcha,
        post_timeout=db_guild.post_timeout,
        max_message_length=db_guild.max_message_length,
        banned_words_enabled=db_guild.banned_words_enabled,
        banned_words_global_included=db_guild.banned_words_global_included,
        banned_words=json.loads(db_guild.banned_words),
        autorole_unauth=db_guild.autorole_unauth,
        autorole_discord=db_guild.autorole_discord,
        file_upload=db_guild.file_upload,
    )

@user.route("/add-bot/<guild_id>")
@discord_users_only()
def add_bot(guild_id):
    session["redirect"] = None
    return render_template("add_bot.html.j2", guild_id=guild_id, guild_invite_url=generate_bot_invite_url(guild_id))

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

@user.route("/ban", methods=["POST"])
@discord_users_only(api=True)
def ban_unauthenticated_user():
    guild_id = request.form.get("guild_id", None)
    user_id = request.form.get("user_id", None)
    reason = request.form.get("reason", None)
    if guild_id in list_disabled_guilds():
        return ('', 423)
    if reason is not None:
        reason = reason.strip()
        if reason == "":
            reason = None
    if not guild_id or not user_id:
        abort(400)
    if not check_user_permission(guild_id, 2):
        abort(401)
    db_user = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.id == user_id).order_by(UnauthenticatedUsers.id.desc()).first()
    if db_user is None:
        abort(404)
    db_ban = db.session.query(UnauthenticatedBans).filter(UnauthenticatedBans.guild_id == guild_id, UnauthenticatedBans.ip_address == db_user.ip_address).first()
    if db_ban is not None:
        if db_ban.lifter_id is None:
            abort(409)
        db.session.delete(db_ban)
    db_ban = UnauthenticatedBans(guild_id, db_user.ip_address, db_user.username, db_user.discriminator, reason, session["user_id"])
    db.session.add(db_ban)
    db.session.commit()
    return ('', 204)

@user.route("/ban", methods=["DELETE"])
@discord_users_only(api=True)
def unban_unauthenticated_user():
    guild_id = request.args.get("guild_id", None)
    user_id = request.args.get("user_id", None)
    if guild_id in list_disabled_guilds():
        return ('', 423)
    if not guild_id or not user_id:
        abort(400)
    if not check_user_permission(guild_id, 2):
        abort(401)
    db_user = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.id == user_id).order_by(UnauthenticatedUsers.id.desc()).first()
    if db_user is None:
        abort(404)
    db_ban = db.session.query(UnauthenticatedBans).filter(UnauthenticatedBans.guild_id == guild_id, UnauthenticatedBans.ip_address == db_user.ip_address).first()
    if db_ban is None:
        abort(404)
    if db_ban.lifter_id is not None:
        abort(409)
    db_ban.liftBan(session["user_id"])
    db.session.commit()
    return ('', 204)

@user.route("/revoke", methods=["POST"])
@discord_users_only(api=True)
def revoke_unauthenticated_user():
    guild_id = request.form.get("guild_id", None)
    user_id = request.form.get("user_id", None)
    if guild_id in list_disabled_guilds():
        return ('', 423)
    if not guild_id or not user_id:
        abort(400)
    if not check_user_permission(guild_id, 1):
        abort(401)
    db_user = db.session.query(UnauthenticatedUsers).filter(UnauthenticatedUsers.guild_id == guild_id, UnauthenticatedUsers.id == user_id).order_by(UnauthenticatedUsers.id.desc()).first()
    if db_user is None:
        abort(404)
    if db_user.isRevoked():
        abort(409)
    db_user.revokeUser()
    db.session.commit()
    return ('', 204)

@user.route('/donate', methods=["GET"])
@discord_users_only()
def donate_get():
    cosmetics = db.session.query(Cosmetics).filter(Cosmetics.user_id == session["user_id"]).first()
    return render_template('donate.html.j2', cosmetics=cosmetics)

def get_paypal_api():
    return paypalrestsdk.Api({
        'mode': 'sandbox' if app.config["DEBUG"] else 'live',
        'client_id': config["paypal-client-id"],
        'client_secret': config["paypal-client-secret"]})

@user.route('/donate', methods=['POST'])
@discord_users_only()
def donate_post():
    donation_amount = request.form.get('amount')
    if not donation_amount:
        abort(402)
        
    donation_amount = float(donation_amount)
    if donation_amount < 5 or donation_amount > 100:
        abort(412)

    donation_amount = "{0:.2f}".format(donation_amount)
    payer = {"payment_method": "paypal"}
    items = [{"name": "TitanEmbeds Donation",
              "price": donation_amount,
              "currency": "USD",
              "quantity": "1"}]
    amount = {"total": donation_amount,
              "currency": "USD"}
    description = "Donate and support TitanEmbeds development."
    redirect_urls = {"return_url": url_for('user.donate_confirm', success="true", _external=True),
                     "cancel_url": url_for('index', _external=True)}
    payment = paypalrestsdk.Payment({"intent": "sale",
                                     "payer": payer,
                                     "redirect_urls": redirect_urls,
                                     "transactions": [{"item_list": {"items":
                                                                     items},
                                                       "amount": amount,
                                                       "description":
                                                       description}]}, api=get_paypal_api())
    if payment.create():
        for link in payment.links:
            if link['method'] == "REDIRECT":
                return redirect(link["href"])
    return redirect(url_for('index'))
    
@user.route("/donate/confirm")
@discord_users_only()
def donate_confirm():
    if not request.args.get('success'):
        return redirect(url_for('index'))
    payment = paypalrestsdk.Payment.find(request.args.get('paymentId'), api=get_paypal_api())
    if payment.execute({"payer_id": request.args.get('PayerID')}):
        trans_id = str(payment.transactions[0]["related_resources"][0]["sale"]["id"])
        amount = float(payment.transactions[0]["amount"]["total"])
        tokens = int(amount * 100)
        action = "PAYPAL {}".format(trans_id)
        set_titan_token(session["user_id"], tokens, action)
        session["tokens"] = get_titan_token(session["user_id"])
        add_badge(session["user_id"], "supporter")
        db.session.commit()
        return redirect(url_for('user.donate_thanks', transaction=trans_id))
    else:
        return redirect(url_for('index'))

@user.route("/donate/thanks")
@discord_users_only()
def donate_thanks():
    tokens = get_titan_token(session["user_id"])
    transaction = request.args.get("transaction")
    return render_template("donate_thanks.html.j2", tokens=tokens, transaction=transaction)

@user.route('/donate', methods=['PATCH'])
@discord_users_only()
def donate_patch():
    item = request.form.get('item')
    amount = int(request.form.get('amount'))
    if amount <= 0:
        abort(400)
    subtract_amt = 0
    entry = db.session.query(Cosmetics).filter(Cosmetics.user_id == session["user_id"]).first()
    if item == "custom_css_slots":
        subtract_amt = 100
    if item == "guest_icon":
        subtract_amt = 300
        if entry is not None and entry.guest_icon:
            abort(400)
    amt_change = -1 * subtract_amt * amount
    subtract = set_titan_token(session["user_id"], amt_change, "BUY " + item + " x" + str(amount))
    if not subtract:
        return ('', 402)
    session["tokens"] += amt_change
    if item == "custom_css_slots":
        if not entry:
            entry = Cosmetics(session["user_id"])
            entry.css_limit = 0
        entry.css = True
        entry.css_limit += amount
    if item == "guest_icon":
        if not entry:
            entry = Cosmetics(session["user_id"])
        entry.guest_icon = True
    db.session.add(entry)
    db.session.commit()
    return ('', 204)

@user.route("/patreon")
@discord_users_only()
def patreon_landing():
    return render_template("patreon.html.j2", pclient_id=config["patreon-client-id"], state="initial")

@user.route("/patreon/callback")
@discord_users_only()
def patreon_callback():
    patreon_oauth_client = patreon.OAuth(config["patreon-client-id"], config["patreon-client-secret"])
    tokens = patreon_oauth_client.get_tokens(request.args.get("code"), url_for("user.patreon_callback", _external=True))
    if "error" in tokens:
        if "patreon" in session:
            del session["patreon"]
        return redirect(url_for("user.patreon_landing"))
    session["patreon"] = tokens
    return redirect(url_for("user.patreon_sync_get"))

def format_patreon_user(user):
    pledges = []
    for pledge in user.relationship('pledges'):
        pledges.append({
            "id": pledge.id(),
            "attributes": pledge.attributes(),
        })
    usrobj = {
        "id": user.id(),
        "attributes": user.attributes(),
        "pledges": pledges,
        "titan": {
            "eligible_tokens": 0,
            "total_cents_synced": 0,
            "total_cents_pledged": 0,
        },
    }
    if usrobj["pledges"]:
        usrobj["titan"]["total_cents_pledged"] = usrobj["pledges"][0]["attributes"]["total_historical_amount_cents"]
    dbpatreon = db.session.query(Patreon).filter(Patreon.user_id == user.id()).first()
    if dbpatreon:
        usrobj["titan"]["total_cents_synced"] = dbpatreon.total_synced
    usrobj["titan"]["eligible_tokens"] = usrobj["titan"]["total_cents_pledged"] - usrobj["titan"]["total_cents_synced"]
    return usrobj

@user.route("/patreon/sync", methods=["GET"])
@discord_users_only()
def patreon_sync_get():
    if "patreon" not in session:
        return redirect(url_for("user.patreon_landing"))
    api_client = patreon.API(session["patreon"]["access_token"])
    user_response = api_client.fetch_user(None, {
        'pledge': ["amount_cents", "total_historical_amount_cents", "declined_since", "created_at", "pledge_cap_cents", "patron_pays_fees", "outstanding_payment_amount_cents"]
    })
    user = user_response.data()
    if not (user):
        del session["patreon"]
        return redirect(url_for("user.patreon_landing"))
    return render_template("patreon.html.j2", state="prepare", user=format_patreon_user(user))

@user.route("/patreon/sync", methods=["POST"])
@discord_users_only()
def patreon_sync_post():
    if "patreon" not in session:
        abort(401)
    api_client = patreon.API(session["patreon"]["access_token"])
    user_response = api_client.fetch_user(None, {
        'pledge': ["amount_cents", "total_historical_amount_cents", "declined_since", "created_at", "pledge_cap_cents", "patron_pays_fees", "outstanding_payment_amount_cents"]
    })
    user = user_response.data()
    if not (user):
        abort(403)
    usr = format_patreon_user(user)
    if usr["titan"]["eligible_tokens"] <= 0:
        return ('', 402)
    dbpatreon = db.session.query(Patreon).filter(Patreon.user_id == usr["id"]).first()
    if not dbpatreon:
        dbpatreon = Patreon(usr["id"])
    dbpatreon.total_synced = usr["titan"]["total_cents_pledged"]
    db.session.add(dbpatreon)
    set_titan_token(session["user_id"], usr["titan"]["eligible_tokens"], "PATREON {} [{}]".format(usr["attributes"]["full_name"], usr["id"]))
    add_badge(session["user_id"], "supporter")
    session["tokens"] = get_titan_token(session["user_id"])
    db.session.commit()
    return ('', 204)

@user.route("/patreon/thanks")
@discord_users_only()
def patreon_thanks():
    return render_template("patreon.html.j2", state="thanks")