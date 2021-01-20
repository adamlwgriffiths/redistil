import unittest
from redis_mock import Redis
from redistil.pipeline import PromisePipeline

class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.redis = Redis()

    def tearDown(self):
        self.redis.flushall()

    def test_functions(self):
        self.redis.hset('hash', 'field1', '1')
        self.redis.hset('hash', 'field2', '2')
        self.redis.sadd('set', 'a')
        self.redis.sadd('set', 'b')

        p = PromisePipeline(self.redis)

        field1 = p.hget('hash', 'field1')
        field2 = p.hget('hash', 'field2')

        p.delete('set')
        p.sadd('set', 1)
        p.sadd('set', 2)
        s = p.smembers('set')

        p.hset('hash', 'field1', 'a')
        p.hset('hash', 'field2', 'b')

        # pipeline shouldn't have executed yet
        # check the original values still exist
        # redis turns everything to bytes
        self.assertEqual(self.redis.hget('hash', 'field1'), b'1')
        self.assertEqual(self.redis.hget('hash', 'field2'), b'2')
        self.assertEqual(self.redis.smembers('set'), {b'a', b'b'})

        p.execute()

        # check the pipeline modified the database
        # and that the promises all return the correct values
        self.assertEqual(field1.value, b'1')
        self.assertEqual(field2.value, b'2')
        self.assertEqual(s.value, {b'1', b'2'})
        self.assertEqual(self.redis.hget('hash', 'field1'), b'a')
        self.assertEqual(self.redis.hget('hash', 'field2'), b'b')
