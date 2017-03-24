#!/usr/bin/env python2
from titanembeds.app import app

if __name__ == "__main__":
    import os
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # Testing oauthlib
    app.run(host="0.0.0.0",port=3000,debug=True)
