import cv2
import picamera
import numpy as np
from datetime import datetime
import os
from threading import Thread
import time

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
        self.image = np.empty((self.cam.resolution[1], self.cam.resolution[0]), dtype=np.uint8)  
        self.next_image_rgb = np.empty((self.cam.resolution[1], self.cam.resolution[0], 3), dtype=np.uint8)
        self.next_image_bw = None
        self.output_dir = os.path.join('/home/pi/projects/pi-tracker/web/images', datetime.now().strftime("%Y-%m-%d.%H:%M:%S"))
        os.mkdir(self.output_dir)
        self.output_count = 0
        self.enableSaving = False
        self.image_is_available = False
        
        self.capture_thread = Thread(target = self.capture_loop)
        self.capture_thread.start()

        #make black/white
        
    def capture_loop(self):
        while 1:
            self.cam.capture(self.next_image_rgb, 'rgb')
            #print(self.next_image_rgb.shape)
            
            self.next_image_bw = self.next_image_rgb[:, :, 0]
            #process?
            self.image = self.next_image_bw
            self.image_is_available = True
    
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
        while not self.image_is_available:
            time.sleep(0.001)
            
        ret, jpeg = cv2.imencode('.jpg', self.image)
        self.image_is_available = False
        
        if self.enableSaving:
            f = open(os.path.join(self.output_dir, str(self.output_count) + '.jpg'), 'wb')
            f.write(jpeg)
            f.close()
            self.output_count += 1
        #print(type(jpeg))
        return jpeg
