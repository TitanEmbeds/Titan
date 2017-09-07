from run import app, socketio, init_debug
import os

if __name__ == "__main__":
    init_debug()
    socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)), debug=True)