import urlparse
from limits.storage import Storage
from redislite import Redis
import time

class LimitsRedisLite(Storage): # For Python Limits
    STORAGE_SCHEME = "redislite"
    def __init__(self, uri, **options):
        self.redis_instance = Redis(urlparse.urlparse(uri).netloc)

    def check(self):
        return True

    def get_expiry(self, key):
        return (self.redis_instance.ttl(key) or 0) + time.time()

    def incr(self, key, expiry, elastic_expiry=False):
        if not self.redis_instance.exists(key):
            self.redis_instance.set(key, 1)
            self.redis_instance.expireat(key, int(time.time() + expiry))
        else:
            oldexp = self.get_expiry(key)
            self.redis_instance.set(key, int(self.redis_instance.get(key))+1)
            self.redis_instance.expireat(key, int(time.time() + oldexp))
        return

    def get(self, key):
        return int(self.redis_instance.get(key))

    def reset(self):
        return self.redis_instance.flushdb()
