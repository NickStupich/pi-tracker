#!/usr/bin/env python3

import struct
import redis
import numpy as np

def toRedis(a):
   """Store given Numpy array 'a' in Redis under key 'n'"""
   h, w = a.shape
   shape = struct.pack('>II',h,w)
   encoded = shape + a.tobytes()

   return encoded

def fromRedis(encoded, dtype):
   """Retrieve Numpy array from Redis key 'n'"""
   # encoded = r.get(n)
   h, w = struct.unpack('>II',encoded[:8])
   a = np.frombuffer(encoded, dtype=np.uint8, offset=8).reshape(h,w)
   return a


def test():
   # Create 80x80 numpy array to store
   a0 = np.arange(6400,dtype=np.uint16).reshape(80,80) 

   # Redis connection
   r = redis.Redis(host='localhost', port=6379, db=0)

   # Store array a0 in Redis under name 'a0array'
   toRedis(r,a0,'a0array')

   # Retrieve from Redis
   a1 = fromRedis(r,'a0array')

   np.testing.assert_array_equal(a0,a1)