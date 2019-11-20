import numpy as np

import redis
import redis_helpers

import messages
import cv2

class ImagePreview(object):
	def __init__(self):		
		self.visual_gain = 10 #TODO: one place?
		self.r = redis.StrictRedis(host='localhost', port=6379) 
		p = self.r.pubsub(ignore_subscribe_messages=True)
		self.kill = False
		p.subscribe(**{messages.STOP_ALL:self.stop_all_handler,
				messages.CMD_SET_VISUAL_GAIN : self.set_visual_gain_handler,
				messages.NEW_IMAGE_FRAME : self.new_image_frame_handler,
				messages.NEW_SUB_IMAGE_FRAME : self.new_sub_image_frame_handler,
			})

		self.thread =  p.run_in_thread(sleep_time = 0.1)

	def stop_all_handler(self, message):
		self.thread.stop()

	def set_visual_gain_handler(self, message):
		new_gain = redis_helpers.fromRedis(message['data'])
		self.visual_gain = new_gain

	def new_image_frame_handler(self, message):
		jpeg_bytes = self.message_to_scaled_jpeg_bytes(message)
		self.r.publish(messages.NEW_PREVIEW_FRAME, redis_helpers.toRedis(jpeg_bytes))

	def new_sub_image_frame_handler(self, message):
		jpeg_bytes = self.message_to_scaled_jpeg_bytes(message)
		self.r.publish(messages.NEW_SUB_PREVIEW_FRAME, redis_helpers.toRedis(jpeg_bytes))

	def message_to_scaled_jpeg_bytes(self, message):

		image = redis_helpers.fromRedis(message['data'])

		target_size = 400
		if image.shape[0] > target_size:
			factor = image.shape[0] // target_size
			image = cv2.resize(image, None, fx = 1.0 / factor, fy = 1.0 / factor, interpolation=cv2.INTER_AREA)

		output_image = image * self.visual_gain

		ret, jpeg = cv2.imencode('.jpg', output_image)
		jpeg_bytes = jpeg.tobytes()
		return jpeg_bytes

