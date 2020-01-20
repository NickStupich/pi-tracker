import numpy as np
# import matplotlib.pyplot as plt

import threading
import time

import messages

import redis
import redis_helpers


class Ditherer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
 
    def run(self):
        self.r = redis.StrictRedis(host='localhost', port=6379) 
        p = self.r.pubsub(ignore_subscribe_messages=True)

        self.t = 0
        self.dithering_magnitude_pixels = 1
        self.dithering_interval_seconds = 30
        self.dithering_enabled = False
        self.kill = False

        p.subscribe(**{messages.STOP_ALL : self.stop_all_handler,
        	messages.CMD_START_GUIDING : self.start_guiding_handler,
        	messages.CMD_SET_DITHERING_MAGNITUDE: self.set_dithering_magnitude_handler,
        	messages.CMD_SET_DITHERING_INTERVAL : self.set_dithering_interval_handler,
        	messages.CMD_START_DITHERING : self.start_dithering_handler,
        	messages.CMD_STOP_DITHERING : self.stop_dithering_handler,
        	messages.STATUS_GET_ALL_STATUS : self.get_status_handler,
        	})

        self.thread = p.run_in_thread(sleep_time = 0.1)

        scale_constant_divider = 5

        while not self.kill:

        	if not self.dithering_enabled:
        		time.sleep(0.5) #don't take too long to get started
        	else:
	        	self.t += 1 / (self.t + 1)
	        	dx = self.t * self.dithering_magnitude_pixels/scale_constant_divider * np.cos(self.t)
	        	dy = self.t * self.dithering_magnitude_pixels/scale_constant_divider * np.sin(self.t)

	        	dither_vector = np.array([dy, dx])
	        	# print('dither vector: ', dither_vector)
	        	self.r.publish(messages.CMD_SET_DITHERING_POSITION_OFFSET_PIXELS, redis_helpers.toRedis(dither_vector))

	        	#at end to reduce race condition when stopping
	        	time.sleep(self.dithering_interval_seconds)

        self.thread.stop()

    def get_status_handler(self, message):
    	self.r.publish(messages.STATUS_DITHERING_STATUS, redis_helpers.toRedis(self.dithering_enabled))

    def stop_all_handler(self, message):
    	self.kill = True

    def start_guiding_handler(self, message):
    	self.t = 0
    	print('restarted dithering')

    def set_dithering_magnitude_handler(self, message):
    	self.t = 0
    	self.dithering_magnitude_pixels = redis_helpers.fromRedis(message['data'])
    	print('dithering magnitude: ', self.dithering_magnitude_pixels)

    def set_dithering_interval_handler(self, message):
    	self.t = 0
    	self.dithering_interval_seconds = redis_helpers.fromRedis(message['data'])
    	print('dithering interval: ', self.dithering_interval_seconds)

    def start_dithering_handler(self, message):
    	self.t = 0
    	self.dithering_enabled = True

    def stop_dithering_handler(self, message):
    	self.dithering_enabled = False
    	self.r.publish(messages.CMD_SET_DITHERING_POSITION_OFFSET_PIXELS, redis_helpers.toRedis(np.array([0, 0])))


def test_actor():
	import matplotlib.pyplot as plt
	d = Ditherer()
	d.start()

	r = redis.StrictRedis(host='localhost', port=6379) 
	xs = []
	ys = []

	def dither_offset_handler(message):
		offsets = redis_helpers.fromRedis(message['data'])
		# print(offsets)
		xs.append(offsets[1])
		ys.append(offsets[0])

	p = r.pubsub(ignore_subscribe_messages=True)
	p.subscribe(**{messages.CMD_SET_DITHERING_POSITION_OFFSET_PIXELS: dither_offset_handler})
	thread = p.run_in_thread(sleep_time=0.1)

	time.sleep(1)

	r.publish(messages.CMD_SET_DITHERING_MAGNITUDE, redis_helpers.toRedis(1))
	r.publish(messages.CMD_SET_DITHERING_INTERVAL, redis_helpers.toRedis(0.01))

	time.sleep(30)

	r.publish(messages.STOP_ALL, "")

	plt.plot(xs, ys, '--o')
	plt.grid(True)
	plt.show()

def test_equation():

	import matplotlib.pyplot as plt
	xs = []
	ys = []

	a = 0
	b = 0.5 # b = euclidean distance between successive points
	t = 0
	for i in range(1800):

		# phase = np.log(i+1)
		# radius = np.log(i+1)

		# t = np.sqrt(i)
		# t += 1/(i+1)
		t += 1/(t+1)
		x = (a + b*t) * np.cos(t)
		y = (a + b*t) * np.sin(t)

		# x = radius * np.sin(phase)
		# y = radius * np.cos(phase)

		xs.append(x)
		ys.append(y)

	distances = []
	for i in range(len(xs)-1):
		d = np.sqrt((xs[i+1] - xs[i])**2 + (ys[i+1] - ys[i])**2)
		distances.append(d)

	plt.plot(distances)
	plt.show()

	plt.plot(xs, ys, '--o')
	plt.grid(True)
	plt.show()


if __name__ == "__main__":
	# test_equation()

	test_actor()
