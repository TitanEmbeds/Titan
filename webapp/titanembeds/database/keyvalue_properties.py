from titanembeds.database import db
from datetime import datetime, timedelta
from limits.storage import Storage
import time

def set_keyvalproperty(key, value, expiration=None):
    q = db.session.query(KeyValueProperties).filter(KeyValueProperties.key == key)
    if q.count() == 0:
        db.session.add(KeyValueProperties(key=key, value=value, expiration=expiration))
    else:
        if expiration is not None:
            converted_expr = datetime.fromtimestamp(time.time() + expiration)
        else:
            converted_expr = None
        firstobj = q.first()
        firstobj.value = value
        firstobj.expiration = converted_expr
    db.session.commit()

def get_keyvalproperty(key):
    q = db.session.query(KeyValueProperties).filter(KeyValueProperties.key == key)
    now = datetime.now()
    if q.count() > 0 and (q.first().expiration.replace(tzinfo=None) is None or q.first().expiration.replace(tzinfo=None) > now.replace(tzinfo=None)):
        return q.first().value
    return None

def getexpir_keyvalproperty(key):
    q = db.session.query(KeyValueProperties).filter(KeyValueProperties.key == key)
    now = datetime.now()
    if q.count() > 0 and (q.first().expiration.replace(tzinfo=None) is not None and q.first().expiration.replace(tzinfo=None) > now.replace(tzinfo=None)):
        return int(q.first().expiration.strftime('%s'))
    return 0

def setexpir_keyvalproperty(key, expiration=None):
    q = db.session.query(KeyValueProperties).filter(KeyValueProperties.key == key)
    if q.count() > 0:
        if expiration:
            q.first().expiration = datetime.now()
        else:
            q.first().expiration = None
        db.session.commit()

def ifexists_keyvalproperty(key):
    q = db.session.query(KeyValueProperties).filter(KeyValueProperties.key == key)
    return q.count() > 0

def delete_keyvalproperty(key):
    q = db.session.query(KeyValueProperties).filter(KeyValueProperties.key == key).first()
    if q:
        db.session.delete(q)
        db.session.commit()

class KeyValueProperties(db.Model):
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


class LimitsKeyValueProperties(Storage): # For Python Limits
    STORAGE_SCHEME = "keyvalprops"
    def __init__(self, uri, **options):
        pass

    def check(self):
        return True

    def get_expiry(self, key):
        return getexpir_keyvalproperty(key) + time.time()

    def incr(self, key, expiry, elastic_expiry=False):
        if not ifexists_keyvalproperty(key):
            set_keyvalproperty(key, 1, expiration=expiry)
        else:
            oldexp = getexpir_keyvalproperty(key) - time.time()
            if oldexp <= 0:
                delete_keyvalproperty(key)
                return self.incr(key, expiry, elastic_expiry)
            set_keyvalproperty(key, int(get_keyvalproperty(key))+1, expiration=int(round(oldexp)))
        return int(self.get(key))

    def get(self, key):
        value = get_keyvalproperty(key)
        if value:
            return int(value)
        return 0

    def reset(self):
        return False
