from config import config
from .database import db
from flask import Flask, render_template, request, session, url_for, redirect, jsonify
from flask_sslify import SSLify
from titanembeds.utils import rate_limiter, discord_api, socketio, babel, redis_store, language_code_list
from .blueprints import api, user, admin, embed, gateway
import os
from titanembeds.database import get_administrators_list
import titanembeds.constants as constants
from datetime import timedelta

try:
    import uwsgi
    from gevent import monkey
    monkey.patch_all()
except:
    if config.get("websockets-mode", None) == "eventlet":
        import eventlet
        eventlet.monkey_patch()
    elif config.get("websockets-mode", None) == "gevent":
        from gevent import monkey
        monkey.patch_all()

os.chdir(config['app-location'])
app = Flask(__name__, static_folder="static")
app.config['SQLALCHEMY_DATABASE_URI'] = config['database-uri']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress the warning/no need this on for now.
app.config['RATELIMIT_HEADERS_ENABLED'] = True
app.config['SQLALCHEMY_POOL_RECYCLE'] = 250
app.config['SQLALCHEMY_POOL_SIZE'] = 100
app.config['RATELIMIT_STORAGE_URL'] = config["redis-uri"]
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=3)
app.config['REDIS_URL'] = config["redis-uri"]
app.secret_key = config['app-secret']

db.init_app(app)
rate_limiter.init_app(app)
if config.get("enable-ssl", False):
    sslify = SSLify(app, permanent=True)
socketio.init_app(app, message_queue=config["redis-uri"], path='gateway', async_mode=config.get("websockets-mode", None))
babel.init_app(app)
redis_store.init_app(app)

app.register_blueprint(api.api, url_prefix="/api", template_folder="/templates")
app.register_blueprint(admin.admin, url_prefix="/admin", template_folder="/templates")
app.register_blueprint(user.user, url_prefix="/user", template_folder="/templates")
app.register_blueprint(embed.embed, url_prefix="/embed", template_folder="/templates")
socketio.on_namespace(gateway.Gateway('/gateway'))

@babel.localeselector
def get_locale():
    param_lang = request.args.get("lang", None)
    if param_lang in language_code_list():
        return param_lang
    return request.accept_languages.best_match(language_code_list())

@app.route("/")
def index():
    return render_template("index.html.j2")

@app.route("/about")
def about():
    return render_template("about.html.j2")

@app.route("/terms")
def terms():
    return render_template("terms_and_conditions.html.j2")

@app.route("/privacy")
def privacy():
    return render_template("privacy_policy.html.j2")

@app.before_first_request
def before_first_request():
    discord_api.init_discordrest()

@app.context_processor
def context_processor():
    return {"devs": get_administrators_list(), "constants": constants}
