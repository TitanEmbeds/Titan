from titanembeds.utils import socketio
from flask_socketio import Namespace, emit

class Gateway(Namespace):
    def on_connect(self):
        emit('key', {'data': 'Connected', 'best_pone': "rainbow"})