import cv2
import picamera
import numpy as np

class VideoCamera(object):
    def __init__(self, cam_num = 0):
        self.cam = picamera.PiCamera()
        self.cam.resolution = (320,240)
        #make black/white
    
    def __del__(self):
        self.cam.close()
    
    def get_frame(self):
        #success, image = self.video.read()
        image = np.empty((240, 320, 3), dtype=np.uint8)	
        self.cam.capture(image, 'rgb')
        #print(image.shape, image.dtype)
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()
