from titanembeds.database import db

class UnauthenticatedUsers(db.Model):
    __tablename__ = "unauthenticated_users"
    id = db.Column(db.Integer, primary_key=True)    # Auto increment id
    guild_id = db.Column(db.BigInteger)            # Guild pretaining to the unauthenticated user
    username = db.Column(db.String(255))            # The username of the user
    discriminator = db.Column(db.Integer)           # The discriminator to distinguish unauth users with each other
    user_key = db.Column(db.Text())                 # The secret key used to identify the user holder
    ip_address = db.Column(db.String(255))          # The IP Address of the user
    revoked = db.Column(db.Boolean())               # If the user's key has been revoked and a new one is required to be generated