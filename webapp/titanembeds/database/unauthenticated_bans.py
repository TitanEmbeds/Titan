from titanembeds.database import db
import datetime
import time

class UnauthenticatedBans(db.Model):
    __tablename__ = "unauthenticated_bans"
    id = db.Column(db.Integer, primary_key=True)                    # Auto increment id
    guild_id = db.Column(db.BigInteger, nullable=False)            # Guild pretaining to the unauthenticated user
    ip_address = db.Column(db.String(255), nullable=False)          # The IP Address of the user
    last_username = db.Column(db.String(255), nullable=False)       # The username when they got banned
    last_discriminator = db.Column(db.Integer, nullable=False)      # The discrim when they got banned
    timestamp = db.Column(db.TIMESTAMP, nullable=False)             # The timestamp of when the user got banned
    reason = db.Column(db.Text())                                   # The reason of the ban set by the guild moderators
    lifter_id = db.Column(db.BigInteger)                           # Discord Client ID of the user who lifted the ban
    placer_id = db.Column(db.BigInteger, nullable=False)           # The id of who placed the ban

    def __init__(self, guild_id, ip_address, last_username, last_discriminator, reason, placer_id):
        self.guild_id = guild_id
        self.ip_address = ip_address
        self.last_username = last_username
        self.last_discriminator = last_discriminator
        self.timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        self.reason = reason
        self.lifter_id = None
        self.placer_id = placer_id

    def liftBan(self, lifter_id):
        self.lifter_id = lifter_id
        return self.lifter_id

    def __repr__(self):
        return '<UnauthenticatedBans {0} {1} {2} {3} {4} {5}'.format(self.id, self.guild_id, self.ip_address, self.last_username, self.last_discriminator, self.timestamp)
