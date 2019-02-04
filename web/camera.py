import time
from base_camera import BaseCamera
import os
import cv2

base_shutter_speed = 100

def load_image(filename):
	# print('loading ', filename)
	result = cv2.imread(filename, 0)

	# f_ratio = 0.5
	# result = cv2.resize(result, None, fx = f_ratio, fy = f_ratio)

	return result

class Camera(BaseCamera):

    @staticmethod
    def frames():

        # folder = 'F:/star_guiding/test_frames'
        folder = 'D:/star_guiding/test_frames'

        filenames = list(map(lambda s2: os.path.join(folder, s2), filter(lambda s: s.startswith('IMG'), os.listdir(folder))))
        imgs = [None for file in filenames]

        count = 0
        while True:
            time.sleep(0.5)

            index = count % len(imgs)
            if (count // len(imgs)) % 2 > 0: #flip around backwards for continuity
                index = len(imgs) - index - 1

            if imgs[index] is None:
            	imgs[index] = load_image(filenames[index])

            img = imgs[index]
            count += 1

            if BaseCamera.shutter_speed_ms != base_shutter_speed:
            	img = img * BaseCamera.shutter_speed_ms / base_shutter_speed

            # print('camera returning frame')

            yield img.copy()
