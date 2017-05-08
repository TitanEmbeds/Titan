from titanembeds.database import db
import datetime
import time
import random
import string

class UnauthenticatedUsers(db.Model):
    __tablename__ = "unauthenticated_users"
    id = db.Column(db.Integer, primary_key=True)    # Auto increment id
    guild_id = db.Column(db.String(255))            # Guild pretaining to the unauthenticated user
    username = db.Column(db.String(255))            # The username of the user
    discriminator = db.Column(db.Integer)           # The discriminator to distinguish unauth users with each other
    user_key = db.Column(db.Text())                 # The secret key used to identify the user holder
    ip_address = db.Column(db.String(255))          # The IP Address of the user
    last_timestamp = db.Column(db.TIMESTAMP)        # The timestamp of when the user has last sent the heartbeat
    revoked = db.Column(db.Boolean())               # If the user's key has been revoked and a new one is required to be generated

    def __init__(self, guild_id, username, discriminator, ip_address):
        self.guild_id = guild_id
        self.username = username
        self.discriminator = discriminator
        self.user_key = "".join(random.choice(string.ascii_letters) for _ in range(0, 32))
        self.ip_address = ip_address
        self.last_timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        self.revoked = False

    def __repr__(self):
        return '<UnauthenticatedUsers {0} {1} {2} {3} {4} {5} {6} {7}>'.format(self.id, self.guild_id, self.username, self.discriminator, self.user_key, self.ip_address, self.last_timestamp, self.revoked)

    def isRevoked(self):
        return self.revoked

    def changeUsername(self, username):
        self.username = username
        db.session.commit()
        return self.username

    def revokeUser(self):
        self.revoked = True
        db.session.commit()
        return self.revoked

    def bumpTimestamp(self):
        self.last_timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        return self.last_timestamp
