import cv2
import picamera
import numpy as np
from datetime import datetime
import os

class VideoCamera(object):
    def __init__(self, cam_num = 0):
        print('opening a new camera')
        self.shutterSpeed = 100 * 1000#us
        self.iso = 800
        self.cam = picamera.PiCamera()
        self.cam.framerate = 8
        self.cam.shutter_speed = self.shutterSpeed
        self.cam.iso = self.iso
        self.cam.color_effects = (128, 128)
        #self.cam.resolution = (2592, 1952)
        self.cam.resolution = (672, 496)
        self.image = np.empty((self.cam.resolution[1], self.cam.resolution[0], 3), dtype=np.uint8)	
        
        self.output_dir = os.path.join('/home/pi/projects/pi-tracker/web/images', datetime.now().strftime("%Y-%m-%d.%H:%M:%S"))
        os.mkdir(self.output_dir)
        self.output_count = 0
        self.enableSaving = False

        #make black/white
    
    def __del__(self):
        self.cam.close()
   
    def setShutterMicroseconds(self, newSpeed):
        self.shutterSpeed = newSpeed
        self.cam.shutter_speed = self.shutterSpeed

    def getShutterMicroseconds(self):
        return self.shutterSpeed

    def setSavingEnabled(self, enableSaving):
        self.enableSaving = enableSaving

    def get_frame(self):
        self.cam.capture(self.image, 'rgb')
        ret, jpeg = cv2.imencode('.jpg', self.image[:, :, 0])
        if self.enableSaving:
            f = open(os.path.join(self.output_dir, str(self.output_count) + '.jpg'), 'wb')
            f.write(jpeg)
            f.close()
        self.output_count += 1
        return jpeg.tobytes()
