import cv2
import numpy as np
import os
import time

baseShutterSpeed = 50 * 1000 #us

class VideoCamera(object):
    def __init__(self, folder = "F:/star_guiding/test_frames"):
        self.files = [os.path.join(folder, file) for file in os.listdir(folder)]
        self.shutterSpeed = baseShutterSpeed
        self.framerate = 10
        self.index = 0
    
    def __del__(self):
        pass

    def setShutterMicroseconds(self, newSpeed):
        self.shutterSpeed = newSpeed

    def getShutterMicroseconds(self):
        return self.shutterSpeed

    def get_frame(self):
        #success, image = self.video.read()
        image = cv2.imread(self.files[self.index], 0)
        self.index = (self.index + 1 ) % len(self.files)

        image = np.clip((image.astype('float32') * (self.shutterSpeed / baseShutterSpeed)), 0, 255).astype('uint8')
        time.sleep(1. / self.framerate)
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()
