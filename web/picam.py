import cv2
import picamera
import numpy as np

class VideoCamera(object):
    def __init__(self, cam_num = 0):
        self.shutterSpeed = 50 * 1000#us
        self.iso = 800
        self.cam = picamera.PiCamera()
        self.cam.framerate = 10
        self.cam.shutter_speed = self.shutterSpeed
        self.cam.iso = self.iso
        self.cam.color_effects = (128, 128)
        #self.cam.resolution = (2592, 1952)
        self.cam.resolution = (672, 496)

        #make black/white
    
    def __del__(self):
        self.cam.close()
    
    def get_frame(self):
        #success, image = self.video.read()
        image = np.empty((self.cam.resolution[1], self.cam.resolution[0], 3), dtype=np.uint8)	
        self.cam.capture(image, 'rgb')
        #print(image.shape, image.dtype)
        ret, jpeg = cv2.imencode('.jpg', image[:, :, 0])
        return jpeg.tobytes()
