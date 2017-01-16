from config import config
from flask import Flask, render_template, request, jsonify, session, url_for, redirect
import requests
import json

app = Flask(__name__)
app.secret_key = "doafkjgasfjk"

_DISCORD_API_BASE = "https://discordapp.com/api/v6"

@app.route("/api/Get_Channel_Messages")
def get_channel_messages():
    channel_id = request.args.get('channel_id')
    after_snowflake = request.args.get('after', None, type=int)
    _endpoint = _DISCORD_API_BASE + "/channels/{channel_id}/messages".format(channel_id=channel_id)
    payload = {}
    if after_snowflake is not None:
        payload = {'after': after_snowflake}
    headers = {'Authorization': 'Bot ' + config['bot-token']}
    r = requests.get(_endpoint, params=payload, headers=headers)
    return jsonify(j=json.loads(r.content))

@app.route("/api/Create_Message", methods=['POST'])
def post_create_message():
    channel_id = request.form.get('channel_id')
    content = request.form.get('content')
    username = session['username']
    _endpoint = _DISCORD_API_BASE + "/channels/{channel_id}/messages".format(channel_id=channel_id)
    payload = {'content': username + ": " + content}
    headers = {'Authorization': 'Bot ' + config['bot-token'], 'Content-Type': 'application/json'}
    r = requests.post(_endpoint, headers=headers, data=json.dumps(payload))
    return jsonify(j=json.loads(r.content))
    
@app.route("/set_username", methods=["GET"])
def get_set_username():
    return render_template("set_username.html")

@app.route("/set_username", methods=["POST"])
def post_set_username():
    session['username'] = request.form.get('username')
    return redirect(url_for("embed_get", channelid=1))

@app.route("/")
def hello():
    return "This page is not blank"

@app.route("/embed/<channelid>")
def embed_get(channelid):
    if 'username' not in session:
        return redirect(url_for("get_set_username"))
    return render_template("embed.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=3000,debug=True)
