from picamera import mmal, mmalobj as mo
import time
import numpy as np
import cv2

count = 0
filtered_image = None
ema = 0.5

def image_callback(port, buf):
	global count
	global filtered_image
	count += 1
	if len(buf.data) > 0:
		img = np.frombuffer(buf.data, dtype=np.uint8).reshape(1088, 1920, 3)
		#bw_img = np.mean(img, axis=2)/255.
		#bw_img = img[:, :, 1].astype('float32')/255.
		bw_img = img[:, :, 1]
		#bw_img = np.sum(img, axis=2, dtype=np.int32)

		print(bw_img.shape)
		if filtered_image is None:
			filtered_image = bw_img.copy()
		else:
			#filtered_image = filtered_image * ema + bw_img 
			filtered_image = bw_img.copy()
		#cv2.imshow('image', img)
		cv2.imshow('image', filtered_image)
		#cv2.imshow('image', bw_img)
		cv2.waitKey(1)

	return False

def test():
	camera = mo.MMALCamera()
	preview = mo.MMALRenderer()
	#print(dir(mmal))
	
	camera.outputs[0].framesize = (1920, 1080)
	camera.outputs[0].framerate = 5
	camera.outputs[0].format = mmal.MMAL_ENCODING_RGB24

	camera.control.params[mmal.MMAL_PARAMETER_ISO] = 800
	camera.control.params[mmal.MMAL_PARAMETER_SHUTTER_SPEED] = 100000
	print(camera.control.params[mmal.MMAL_PARAMETER_SHUTTER_SPEED])
	
	awb = camera.control.params[mmal.MMAL_PARAMETER_AWB_MODE]
	awb.value = mmal.MMAL_PARAM_AWBMODE_SUNLIGHT
	camera.control.params[mmal.MMAL_PARAMETER_AWB_MODE] = awb

	camera.outputs[0].commit()

	camera.outputs[0].enable(image_callback)
	seconds = 10
	time.sleep(seconds)
	
	camera.control.params[mmal.MMAL_PARAMETER_SHUTTER_SPEED] = 500000
	
	time.sleep(seconds)

	camera.outputs[0].disable()

	global count
	print('fps (ish): ', count / seconds)

if __name__ == "__main__":
	test()
	