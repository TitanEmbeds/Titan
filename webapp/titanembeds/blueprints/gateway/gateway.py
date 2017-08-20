from titanembeds.utils import socketio
from flask_socketio import Namespace, emit, disconnect, join_room
import functools
from flask import request, session

def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if False:
            pass
            #disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped

class Gateway(Namespace):
    def on_connect(self):
        emit('hello')
    
    def on_identify(self, data):
        room = data["guild_id"]
        join_room(room)