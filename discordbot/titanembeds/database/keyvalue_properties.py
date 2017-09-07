from titanembeds.database import db, Base
import datetime

class KeyValueProperties(Base):
    __tablename__ = "keyvalue_properties"
    id = db.Column(db.Integer, primary_key=True)                    # Auto incremented id
    key = db.Column(db.String(255), nullable=False)                 # Property Key
    value = db.Column(db.Text())                                    # Property value
    expiration = db.Column(db.TIMESTAMP)                            # Suggested Expiration for value (None = no expire) in secs

    def __init__(self, key, value, expiration=None):
        self.key = key
        self.value = value
        if expiration:
            self.expiration = datetime.now() + timedelta(seconds = expiration)
        else:
            self.expiration = None