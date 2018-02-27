from titanembeds.database import db
import datetime
import time

class DiscordBotsOrgTransactions(db.Model):
    __tablename__ = "discordbotsorg_transactions"
    id = db.Column(db.Integer, primary_key=True)                    # Auto increment id
    user_id = db.Column(db.BigInteger, nullable=False)              # Discord user id of user
    timestamp = db.Column(db.TIMESTAMP, nullable=False)             # The timestamp of when the action took place
    action = db.Column(db.String(255), nullable=False)              # Very short description of the action
    referrer = db.Column(db.BigInteger, nullable=True)              # Discord user id of the referrer
    
    def __init__(self, user_id, action, referrer=None):
        self.user_id = user_id
        self.action = action
        if referrer:
            self.referrer = referrer
        self.timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')