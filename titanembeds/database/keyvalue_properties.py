from titanembeds.database import db
from datetime import datetime

def set_keyvalproperty(key, value, expiration=None):
    q = db.session.query(KeyValueProperties).filter(KeyValueProperties.key == key)
    if q.count() == 0:
        db.session.add(KeyValueProperties(key=key, value=value, expiration=expiration))
    else:
        firstobj = q.first()
        firstobj.value = value
        firstobj.expiration = expiration
    db.session.commit()

def get_keyvalproperty(key):
    q = db.session.query(KeyValueProperties).filter(KeyValueProperties.key == key)
    now = datetime.now()
    if q.count() > 0 and (q.first().expiration is None or q.first().expiration > now):
        return q.first().value
    return None

def getexpir_keyvalproperty(key):
    q = db.session.query(KeyValueProperties).filter(KeyValueProperties.key == key)
    now = datetime.now()
    if q.count() > 0 and (q.first().expiration is not None and q.first().expiration > now):
        return q.first().expiration
    return None

def setexpir_keyvalproperty(key, expiration=None):
    q = db.session.query(KeyValueProperties).filter(KeyValueProperties.key == key)
    if q.count() > 0:
        if expiration:
            q.first().expiration = datetime.now()
        else:
            q.first().expiration = None
        db.session.commit()

class KeyValueProperties(db.Model):
    __tablename__ = "keyvalue_properties"
    id = db.Column(db.Integer, primary_key=True)    # Auto incremented id
    key = db.Column(db.String(32))                  # Property Key
    value = db.Column(db.Text())                    # Property value
    expiration = db.Column(db.TIMESTAMP)            # Suggested Expiration for value (None = no expire) in secs

    def __init__(self, key, value, expiration=None):
        self.key = key
        self.value = value
        if expiration:
            self.expiration = datetime.datetime.now() + datetime.timedelta(seconds = expiration)
        else:
            self.expiration = None
