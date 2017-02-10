from config import config
from database import db
from flask import Flask, render_template, request, session, url_for, redirect
import blueprints.api
import os


os.chdir(config['app-location'])
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config['database-uri']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress the warning/no need this on for now.
app.secret_key = config['app-secret']

db.init_app(app)

app.register_blueprint(blueprints.api.api, url_prefix="/api", template_folder="/templates")

@app.route("/set_username/<guildid>/<channelid>", methods=["GET"])
def get_set_username(guildid, channelid):
    return render_template("set_username.html")

@app.route("/set_username/<guildid>/<channelid>", methods=["POST"])
def post_set_username(guildid, channelid):
    session['username'] = request.form.get('username')
    return redirect(url_for("embed_get", guildid=guildid, channelid=channelid))

@app.route("/")
def hello():
    return "This page is not blank"

@app.route("/embed/<guildid>/<channelid>")
def embed_get(guildid, channelid):
    if 'username' not in session:
        return redirect(url_for("get_set_username", guildid=guildid, channelid=channelid))
    return render_template("embed.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=3000,debug=True)
