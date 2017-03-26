from config import config
from database import db
from flask import Flask, render_template, request, session, url_for, redirect, jsonify
from titanembeds.utils import cache
import blueprints.api
import blueprints.user
import blueprints.embed
import os


os.chdir(config['app-location'])
app = Flask(__name__, static_folder="static")
app.config['SQLALCHEMY_DATABASE_URI'] = config['database-uri']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress the warning/no need this on for now.
app.secret_key = config['app-secret']

db.init_app(app)
cache.init_app(app, config={'CACHE_TYPE': 'simple'})

app.register_blueprint(blueprints.api.api, url_prefix="/api", template_folder="/templates")
app.register_blueprint(blueprints.user.user, url_prefix="/user", template_folder="/templates")
app.register_blueprint(blueprints.embed.embed, url_prefix="/embed", template_folder="/templates")

@app.route("/set_username/<guildid>/<channelid>", methods=["GET"])
def get_set_username(guildid, channelid):
    return render_template("set_username.html")

@app.route("/set_username/<guildid>/<channelid>", methods=["POST"])
def post_set_username(guildid, channelid):
    session['username'] = request.form.get('username')
    return redirect(url_for("embed_get", guildid=guildid, channelid=channelid))

@app.route("/")
def index():
    return render_template("index.html.j2")

@app.route("/oldembed/<guildid>/<channelid>")
def embed_get(guildid, channelid):
    if 'username' not in session:
        return redirect(url_for("get_set_username", guildid=guildid, channelid=channelid))
    return render_template("embed.html")
