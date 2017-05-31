from run import app, init_debug
import os

if __name__ == "__main__":
    init_debug()
    app.run(host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)), debug=True, processes=3)