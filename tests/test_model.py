import unittest
from datetime import date, datetime
from ipaddress import IPv4Address, IPv6Address
from redis_mock import Redis
from redistil import *

class MyModel(Model):
    string = Field(String, primary_key=True)
    boolean = Field(Boolean)
    integer = Field(Integer)
    float = Field(Float)
    number = Field(Number)
    email = Field(EmailAddress)
    date = Field(Date)
    datetime = Field(DateTime)
    binary = Field(Binary)
    ipv4address = Field(IPV4Address)
    ipv6address = Field(IPV6Address, required=True)
    set = Set(Integer)
    list = List(String)

class TestModel(unittest.TestCase):
    def setUp(self):
        self.redis = Redis()

    def tearDown(self):
        self.redis.flushall()

    def test_key_field(self):
        self.assertEqual(MyModel.key('abc'), 'MyModel::abc')
        self.assertEqual(MyModel.string.field('abc'), 'string')
        self.assertEqual(MyModel.set.key(MyModel.key('abc')), 'MyModel::abc::set')

    def test_create(self):
        # missing primary key
        with self.assertRaises(ValueError):
            model = MyModel.create(self.redis)
        # missing required field ipv6address
        with self.assertRaises(ValueError):
            model = MyModel.create(self.redis,
                string='string',
            )

    def test_create_save_load_delete(self):
        model = MyModel.create(self.redis,
            string='string',
            ipv6address=IPv6Address('::1'),
        )
        self.assertTrue(self.redis.exists(model.redis_key))
        self.assertTrue(self.redis.hexists(model.redis_key, 'string'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'boolean'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'integer'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'float'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'number'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'email'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'date'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'datetime'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'binary'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'ipv4address'))
        self.assertTrue(self.redis.hexists(model.redis_key, 'ipv6address'))
        self.assertFalse(self.redis.exists(model.redis_key + '::set'))
        self.assertFalse(self.redis.exists(model.redis_key + '::list'))

        self.assertEqual(self.redis.hget(model.redis_key, 'string'), b'string')
        self.assertEqual(self.redis.hget(model.redis_key, 'ipv6address'), b'::1')

        today = date.today()
        now = datetime.now()

        # string already set
        model.boolean = True
        model.integer = 123
        model.float = 1.23
        model.number = 456.7
        model.email = 'test@example.com'
        model.date = today
        model.datetime = now
        model.binary = b'123'
        model.ipv4address = IPv4Address('127.0.0.1')
        # ipv6address already set
        model.set = {1, 2, 3}
        model.list = ['a', 'b', 'c']

        # selectively save
        model.save(self.redis, MyModel.boolean)
        self.assertTrue(self.redis.exists(model.redis_key))
        self.assertTrue(self.redis.hexists(model.redis_key, 'string'))
        self.assertTrue(self.redis.hexists(model.redis_key, 'boolean'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'integer'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'float'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'number'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'email'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'date'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'datetime'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'binary'))
        self.assertFalse(self.redis.hexists(model.redis_key, 'ipv4address'))
        self.assertTrue(self.redis.hexists(model.redis_key, 'ipv6address'))
        self.assertFalse(self.redis.exists(model.redis_key + '::set'))
        self.assertFalse(self.redis.exists(model.redis_key + '::list'))

        self.assertEqual(self.redis.hget(model.redis_key, 'string'), b'string')
        self.assertEqual(self.redis.hget(model.redis_key, 'boolean'), b'1')
        self.assertEqual(self.redis.hget(model.redis_key, 'ipv6address'), b'::1')

        # save everything
        model.save(self.redis)
        self.assertTrue(self.redis.exists(model.redis_key))
        self.assertTrue(self.redis.hexists(model.redis_key, 'string'))
        self.assertTrue(self.redis.hexists(model.redis_key, 'boolean'))
        self.assertTrue(self.redis.hexists(model.redis_key, 'integer'))
        self.assertTrue(self.redis.hexists(model.redis_key, 'float'))
        self.assertTrue(self.redis.hexists(model.redis_key, 'number'))
        self.assertTrue(self.redis.hexists(model.redis_key, 'email'))
        self.assertTrue(self.redis.hexists(model.redis_key, 'date'))
        self.assertTrue(self.redis.hexists(model.redis_key, 'datetime'))
        self.assertTrue(self.redis.hexists(model.redis_key, 'binary'))
        self.assertTrue(self.redis.hexists(model.redis_key, 'ipv4address'))
        self.assertTrue(self.redis.hexists(model.redis_key, 'ipv6address'))
        self.assertTrue(self.redis.exists(model.redis_key + '::set'))
        self.assertTrue(self.redis.exists(model.redis_key + '::list'))

        self.assertEqual(self.redis.hget(model.redis_key, 'string'), b'string')
        self.assertEqual(self.redis.hget(model.redis_key, 'boolean'), b'1')
        self.assertEqual(self.redis.hget(model.redis_key, 'integer'), b'123')
        self.assertEqual(self.redis.hget(model.redis_key, 'float'), b'1.23')
        self.assertEqual(self.redis.hget(model.redis_key, 'number'), b'456.7')
        self.assertEqual(self.redis.hget(model.redis_key, 'email'), b'test@example.com')
        self.assertEqual(self.redis.hget(model.redis_key, 'date'), today.isoformat().encode())
        self.assertEqual(self.redis.hget(model.redis_key, 'datetime'), now.isoformat().encode())
        self.assertEqual(self.redis.hget(model.redis_key, 'binary'), b'123')
        self.assertEqual(self.redis.hget(model.redis_key, 'ipv4address'), b'127.0.0.1')
        self.assertEqual(self.redis.hget(model.redis_key, 'ipv6address'), b'::1')
        self.assertEqual(self.redis.smembers(model.redis_key + '::set'), {b'1', b'2', b'3'})
        self.assertEqual(self.redis.lrange(model.redis_key + '::list', 0, -1), [b'a', b'b', b'c'])

        # selective load
        model = MyModel.load(self.redis, 'string', MyModel.boolean)
        self.assertEqual(model.string, 'string')
        self.assertEqual(model.boolean, True)
        self.assertIsNone(model.integer)
        self.assertIsNone(model.float)
        self.assertIsNone(model.number)
        self.assertIsNone(model.email)
        self.assertIsNone(model.date)
        self.assertIsNone(model.datetime)
        self.assertIsNone(model.binary)
        self.assertIsNone(model.ipv4address)
        self.assertIsNone(model.ipv6address)
        self.assertIsNone(model.set)
        self.assertIsNone(model.list)

        # load the remainder
        model.load_fields(self.redis)
        self.assertEqual(model.string, 'string')
        self.assertEqual(model.boolean, True)
        self.assertEqual(model.integer, 123)
        self.assertEqual(model.float, 1.23)
        self.assertEqual(model.number, 456.7)
        self.assertEqual(model.email, 'test@example.com')
        self.assertEqual(model.date, today)
        self.assertEqual(model.datetime, now)
        self.assertEqual(model.binary, b'123')
        self.assertEqual(model.ipv4address, IPv4Address('127.0.0.1'))
        self.assertEqual(model.ipv6address, IPv6Address('::1'))
        self.assertEqual(model.set, {1, 2, 3})
        self.assertEqual(model.list, ['a', 'b', 'c'])

        model.delete(self.redis)
        self.assertFalse(self.redis.exists(model.redis_key))
        self.assertFalse(self.redis.exists(model.redis_key + '::set'))
        self.assertFalse(self.redis.exists(model.redis_key + '::list'))

    def test_delete(self):
        # delete an incomplete field
        model = MyModel.create(self.redis,
            string='string',
            ipv6address=IPv6Address('::1'),
        )

        model.delete(self.redis)
        self.assertFalse(self.redis.exists(model.redis_key))
        self.assertFalse(self.redis.exists(model.redis_key + '::set'))
        self.assertFalse(self.redis.exists(model.redis_key + '::list'))

        # delete non-created object
        model = MyModel(
            string='string',
            ipv6address=IPv6Address('::1'),
        )
        model.delete(self.redis)

    def test_simple_model(self):
        class TestModel(Model):
            string = Field(String, primary_key=True)
            value = Field(String)

        model = TestModel.create(self.redis, string='string')

        model = TestModel(string='string')
        model.save(self.redis)
