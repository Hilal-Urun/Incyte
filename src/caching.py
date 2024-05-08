# caching using redis
import os

from redis import Redis


class RedisCache:
    def __init__(self):
        self.redis = Redis(
            host=os.environ.get("REDIS_HOST"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            password=os.environ.get("REDIS_PASSWORD")
        )

    def set(self, key, value):
        self.redis.set(key, value)

    def get(self, key):
        return self.redis.get(key)

    def delete(self, key):
        self.redis.delete(key)

    def exists(self, key):
        return self.redis.exists(key)

    def flush(self):
        self.redis.flushdb()

    def getOrEval(self, key, callback, *args, **kwargs):
        if self.exists(key):
            return self.get(key)
        else:
            value = callback(*args, **kwargs)
            self.set(key, value)
            return value

    def mgetOrEval(self, keys, callback, *args, **kwargs):
        values = self.redis.mget(keys)
        if not all(values):
            for i, (k, v) in enumerate(zip(keys, values)):
                if not v:
                    values[i] = callback(k, *args, **kwargs)
            self.redis.mset(dict(zip(keys, values)))
        return values


class MemoryCache:
    counter = 0

    def __init__(self):
        self.counter += 1
        print(f"MemoryCache instance {self.counter} created")
        self.cache = {}

    def set(self, key, value):
        self.cache[key] = value

    def get(self, key):
        return self.cache.get(key)

    def delete(self, key):
        del self.cache[key]

    def exists(self, key):
        return key in self.cache

    def flush(self):
        self.cache = {}

    def getOrEval(self, key, callback, *args, **kwargs):
        if self.exists(key):
            return self.get(key)
        else:
            value = callback(*args, **kwargs)
            self.set(key, value)
            return value

    def mgetOrEval(self, keys, callback, *args, **kwargs):
        values = [self.get(k) for k in keys]
        if not all(values):
            for i, (k, v) in enumerate(zip(keys, values)):
                if not v:
                    values[i] = callback(k, *args, **kwargs)
            self.set(keys, values)
        return values


# make it a singleton
cache = RedisCache() if os.environ.get("CACHE_DRIVER", "MEMORY") == "REDIS" else MemoryCache()
