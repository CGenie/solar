from enum import Enum
import json
import redis
import fakeredis

from solar import utils
from solar import errors


class RedisDB(object):
    COLLECTIONS = Enum(
        'Collections',
        'connection resource state_data state_log events'
    )
    DB = {
        'host': 'localhost',
        'port': 6379,
    }
    REDIS_CLIENT = redis.StrictRedis


    def __init__(self):
        self._r = self.REDIS_CLIENT(**self.DB)
        self.entities = {}

    def read(self, uid, collection=COLLECTIONS.resource):
        try:
            return json.loads(
                self._r.get(self._make_key(collection, uid))
            )
        except TypeError:
            return None

    def get_list(self, collection=COLLECTIONS.resource):
        key_glob = self._make_key(collection, '*')

        keys = self._r.keys(key_glob)

        with self._r.pipeline() as pipe:
            pipe.multi()

            values = [self._r.get(key) for key in keys]

            pipe.execute()

        for value in values:
            yield json.loads(value)

    def save(self, uid, data, collection=COLLECTIONS.resource):
        ret = self._r.set(
            self._make_key(collection, uid),
            json.dumps(data)
        )

        return ret

    def save_list(self, lst, collection=COLLECTIONS.resource):
        with self._r.pipeline() as pipe:
            pipe.multi()

            for uid, data in lst:
                key = self._make_key(collection, uid)
                pipe.set(key, json.dumps(data))

            pipe.execute()

    def clear(self):
        self._r.flushdb()

    def get_set(self, collection):
        return OrderedSet(self._r, collection)

    def clear_collection(self, collection=COLLECTIONS.resource):
        key_glob = self._make_key(collection, '*')

        self._r.delete(self._r.keys(key_glob))

    def delete(self, uid, collection=COLLECTIONS.resource):
        self._r.delete(self._make_key(collection, uid))

    def _make_key(self, collection, _id):
        if isinstance(collection, self.COLLECTIONS):
            collection = collection.name

        # NOTE: hiera-redis backend depends on this!
        return '{0}:{1}'.format(collection, _id)


class OrderedSet(object):

    def __init__(self, client, collection):
        self.r = client
        self.collection = collection
        self.order_counter = '{}:incr'.format(collection)
        self.order = '{}:order'.format(collection)

    def add(self, items):
        pipe = self.r.pipeline()
        for key, value in items:
            count = self.r.incr(self.order_counter)
            pipe.zadd(self.order, count, key)
            pipe.hset(self.collection, key, json.dumps(value))
        pipe.execute()

    def rem(self, keys):
        pipe = self.r.pipeline()
        for key in keys:
            pipe.zrem(self.order, key)
            pipe.hdel(self.collection, key)
        pipe.execute()

    def get(self, key):
        value = self.r.hget(self.collection, key)
        if value:
            return json.loads(value)
        return None

    def update(self, key, value):
        self.r.hset(self.collection, key, json.dumps(value))

    def clean(self):
        self.rem(self.r.zrange(self.order, 0, -1))

    def rem_left(self, n=1):
        self.rem(r.zrevrange(self.order, 0, n-1))

    def reverse(self, n=1):
        result = []
        for key in self.r.zrevrange(self.order, 0, n-1):
            result.append(self.get(key))
        return result

    def list(self, n=0):
        result = []
        for key in self.r.zrange(self.order, 0, n-1):
            result.append(self.get(key))
        return result


class FakeRedisDB(RedisDB):

    REDIS_CLIENT = fakeredis.FakeStrictRedis
