import subprocess
if __name__ == "__main__":
    running = subprocess.check_output(['ps', '-A'])
    if "postgres" not in str(running):
        subprocess.call("sudo service postgresql start", shell=True)
        subprocess.call("sudo service redis-server start", shell=True)

from run import app, socketio, init_debug
import os

if __name__ == "__main__":
    init_debug()
    socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)), debug=True)