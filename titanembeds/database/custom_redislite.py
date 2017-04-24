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
            self.redis_instance.set(key, 1, ex=expiry)
        else:
            oldexp = oldexp = self.get_expiry(key) - time.time()
            if oldexp <= 0:
                self.redis_instance.delete(key)
                return self.incr(key, expiry, elastic_expiry)
            self.redis_instance.set(key, int(self.redis_instance.get(key))+1, ex=int(round(oldexp)))
        return int(self.get(key))

    def get(self, key):
        value = self.redis_instance.get(key)
        if value:
            return int(value)
        return 0

    def reset(self):
        return self.redis_instance.flushdb()
