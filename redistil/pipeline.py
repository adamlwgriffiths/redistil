from redis_mock import Redis

class Promise:
    def __init__(self):
        self.value = None
    def set(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)

class PromisePipeline:
    '''Helper for working with Redis.pipeline()
    Returns a promise object which you call .value on after executing the pipeline
    to get the value.
    Saves you having to remember the values position in the command queue.
    '''
    def __init__(self, db, **kwargs):
        self.db = db
        self.pipeline = self.db.pipeline(**kwargs)
        self.promises = []

    def _create_promise(self):
        self.promises.append(Promise())
        return self.promises[-1]

    def hget(self, name, field):
        value = self.pipeline.hget(name, field)
        return self._create_promise()

    def hset(self, name, field, value):
        self.pipeline.hset(name, field, value)
        return self._create_promise()

    def lrange(self, name, start, stop):
        self.pipeline.lrange(name, start, stop)
        return self._create_promise()

    def smembers(self, name):
        self.pipeline.smembers(name)
        return self._create_promise()

    def delete(self, name):
        self.pipeline.delete(name)
        return self._create_promise()

    def rpush(self, name, value):
        self.pipeline.rpush(name, value)
        return self._create_promise()

    def sadd(self, name, value):
        self.pipeline.sadd(name, value)
        return self._create_promise()

    def execute(self):
        values = self.pipeline.execute()
        for promise, value in zip(self.promises, values):
            if isinstance(value, Exception):
                raise value
            promise.set(value)
        return values
