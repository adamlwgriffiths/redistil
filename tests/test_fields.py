import unittest
from datetime import date, datetime
from ipaddress import IPv4Address, IPv6Address
from redis_mock import Redis
from redistil import *

class TestModel(unittest.TestCase):
    def setUp(self):
        self.redis = Redis()

    def tearDown(self):
        self.redis.flushall()

    def test_boolean(self):
        class BooleanModel(Model):
            id = Field(String, primary_key=True)
            boolean = Field(Boolean)

        model = BooleanModel.create(self.redis,
            id='abc',
            boolean=True
        )
        self.assertTrue(self.redis.hexists(model.redis_key, 'boolean'))
        self.assertEqual(self.redis.hget(model.redis_key, 'boolean'), b'1')

        model = BooleanModel.load(self.redis, 'abc')
        self.assertTrue(model.boolean)

        model.boolean = False
        model.save(self.redis)

        self.assertTrue(self.redis.hexists(model.redis_key, 'boolean'))
        self.assertEqual(self.redis.hget(model.redis_key, 'boolean'), b'0')

        model = BooleanModel.load(self.redis, 'abc')
        self.assertFalse(model.boolean)
