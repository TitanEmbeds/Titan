from titanembeds.database import db
import datetime
import time
import random
import string

class UnauthenticatedUsers(db.Model):
    __tablename__ = "unauthenticated_users"
    id = db.Column(db.Integer, primary_key=True, nullable=False)    # Auto increment id
    guild_id = db.Column(db.String(255), nullable=False)            # Guild pretaining to the unauthenticated user
    username = db.Column(db.String(255), nullable=False)            # The username of the user
    discriminator = db.Column(db.Integer, nullable=False)           # The discriminator to distinguish unauth users with each other
    user_key = db.Column(db.Text(), nullable=False)                 # The secret key used to identify the user holder
    ip_address = db.Column(db.String(255), nullable=False)          # The IP Address of the user
    revoked = db.Column(db.Boolean(), nullable=False)               # If the user's key has been revoked and a new one is required to be generated

    def __init__(self, guild_id, username, discriminator, ip_address):
        self.guild_id = guild_id
        self.username = username
        self.discriminator = discriminator
        self.user_key = "".join(random.choice(string.ascii_letters) for _ in range(0, 32))
        self.ip_address = ip_address
        self.revoked = False

    def __repr__(self):
        return '<UnauthenticatedUsers {0} {1} {2} {3} {4} {5} {6}>'.format(self.id, self.guild_id, self.username, self.discriminator, self.user_key, self.ip_address, self.revoked)

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
