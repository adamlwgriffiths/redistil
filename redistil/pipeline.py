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

    def __getattr__(self, name):
        '''Pass function and attribute access through to the Redis pipeline.
        If it's a function, wrap the function in another function that returns a promise.
        If it's not a function, just return it.
        This may not work for everything, but all the functions we care about work so far.
        '''
        if hasattr(self.pipeline, name):
            attr = getattr(self.pipeline, name)

            if not callable(attr):
                return attr

            def wrap(*args, **kwargs):
                attr(*args, **kwargs)
                return self._create_promise()
            return wrap

    def execute(self):
        '''Execute the pipeline, take the resulting values and assign them to each promise.
        '''
        values = self.pipeline.execute()
        for promise, value in zip(self.promises, values):
            if isinstance(value, Exception):
                raise value
            promise.set(value)
        return values
