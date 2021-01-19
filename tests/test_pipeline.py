


'''
redis = Redis()

redis.hset('hash', 'field1', '1')
redis.hset('hash', 'field2', '2')

p = PromisePipeline(redis)
field1 = p.hget('hash', 'field1')
field2 = p.hget('hash', 'field2')
p.delete('set')
p.sadd('set', 1)
p.sadd('set', 2)
s = p.smembers('set')
p.execute()

print(field1.value)
print(field2.value)
print(s.value)
'''
