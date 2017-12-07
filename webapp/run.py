#!/usr/bin/env python2
from titanembeds.app import app, socketio
import subprocess

def init_debug():
    import os
    from flask import jsonify, request

    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # Testing oauthlib
    
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Session viewer https://gist.github.com/babldev/502364a3f7c9bafaa6db
    def decode_flask_cookie(secret_key, cookie_str):
        import hashlib
        from itsdangerous import URLSafeTimedSerializer
        from flask.sessions import TaggedJSONSerializer
        salt = 'cookie-session'
        serializer = TaggedJSONSerializer()
        signer_kwargs = {
            'key_derivation': 'hmac',
            'digest_method': hashlib.sha1
        }
        s = URLSafeTimedSerializer(secret_key, salt=salt, serializer=serializer, signer_kwargs=signer_kwargs)
        return s.loads(cookie_str)

    @app.route("/session")
    def session():
        cookie = request.cookies.get('session')
        if cookie:
            decoded = decode_flask_cookie(app.secret_key, request.cookies.get('session'))
        else:
            decoded = None
        return jsonify(session_cookie=decoded)

    @app.route("/github-update", methods=["POST"])
    def github_update():
        try:
            subprocess.Popen("git pull", shell=True).wait()
        except OSError:
            return "ERROR"

        return "OK"
if __name__ == "__main__":
    init_debug()
    socketio.run(app, host="0.0.0.0",port=3000,debug=True)
