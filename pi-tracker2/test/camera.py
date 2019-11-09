import picamera
import time
from datetime import datetime
import io
from PIL import Image
import numpy as np
import cv2

def test():
	with picamera.PiCamera() as camera:
		camera.raw_format = 'rgb'
		camera.start_preview()
		time.sleep(10)
		camera.stop_preview()	

def test2():
	with picamera.PiCamera() as camera:
		camera.resolution = (2592, 1944)
		start = datetime.now()
		n = 10
		if 0:
			stream = io.BytesIO()
			for i, foo in enumerate(camera.capture_continuous(stream, format='jpeg')):
				stream.truncate()
				stream.seek(0)
				img = np.array(Image.open(stream))
	
				print(img.shape)
				cv2.imshow('image', img)
				cv2.waitKey(1)
				if i >= n: break
		
		elif 1:
	
			camera.raw_format = 'rgb'
			stream = io.BytesIO()
			for i, foo in enumerate(camera.capture_continuous(stream, format='rgb')):
				stream.truncate()
				stream.seek(0)
				img = np.fromstring(stream.getvalue(), dtype=np.uint8)
				img = img.reshape((1952, 2592, 3))
				cv2.imshow('image', img)
				cv2.waitKey(1)
				print(img.shape)
				if i >= n: break
		
		else:
			stream = io.BytesIO()
			for i, foo in enumerate(camera.capture_continuous(stream, format='jpeg')):
				stream.seek(0)
				data = np.fromstring(stream.getvalue(), dtype=np.uint8)
				img = cv2.imdecode(data, 1)
				print(img.shape)
				cv2.imshow('image', img)
				cv2.waitKey(1)
				if i >= n: break

	end = datetime.now()
	print('elapsed time: ', end - start)


if __name__ == "__main__":
	#test()
	test2()