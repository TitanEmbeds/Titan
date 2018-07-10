from titanembeds.database import db
import datetime
import time

class UnauthenticatedBans(db.Model):
    __tablename__ = "unauthenticated_bans"
    id = db.Column(db.Integer, primary_key=True)    # Auto increment id
    guild_id = db.Column(db.String(255))            # Guild pretaining to the unauthenticated user
    ip_address = db.Column(db.String(255))          # The IP Address of the user
    last_username = db.Column(db.String(255))       # The username when they got banned
    last_discriminator = db.Column(db.Integer)      # The discrim when they got banned
    timestamp = db.Column(db.TIMESTAMP)             # The timestamp of when the user got banned
    reason = db.Column(db.Text())                   # The reason of the ban set by the guild moderators
    lifter_id = db.Column(db.BigInteger)           # Discord Client ID of the user who lifted the ban
    placer_id = db.Column(db.BigInteger)           # The id of who placed the ban