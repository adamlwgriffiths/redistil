
'''
class DNS_Record(Model):
    domain = Field(String, primary_key=True)
    A = Field(IPV4Address)
    AAAA = Field(IPV6Address, required=True)
    l = Field(List(String))


from redis_mock import Redis
redis = Redis()


print('create')
r = DNS_Record.create(redis,
    domain='abc.example.com',
    A=IPv4Address('127.0.0.1'),
    AAAA=IPv6Address('::1'),
    l=['a', 'b'])
print(r.domain, r.A, r.AAAA)

print('load')
r = DNS_Record.load(redis, 'abc.example.com')
print(r.domain, r.A, r.AAAA)

r = DNS_Record.load(redis, 'abc.example.com', DNS_Record.A)
print(r.domain, r.A, r.AAAA)

r.A = IPv4Address('10.0.0.1')
r.save(redis, DNS_Record.A)

r = DNS_Record.load(redis, 'abc.example.com', DNS_Record.A)
print(r.domain, r.A, r.AAAA)

r = DNS_Record.load(redis, 'abc.example.com', DNS_Record.A, DNS_Record.l)
print(r.domain, r.A, r.AAAA, r.l)


print(type(r.A))

print(r)
print(repr(r))

try:
    DNS_Record.create(redis, domain='abc', A=123, AAAA=IPv6Address('::1'))
    assert False
except Exception as e:
    print(e)

try:
    DNS_Record.create(redis, domain='abc', A=IPv4Address('127.0.0.1'))
    assert False
except Exception as e:
    print(e)

'''
