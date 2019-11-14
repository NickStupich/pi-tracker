import time
import numpy as np
import cv2
from pubsub import pub
import messages
import threading
import os

BASE_SHUTTER_SPEED_MS = 10

def load_image(filename):
    print('loading ', filename)
    result = cv2.imread(filename, 0)

    return result

class Camera(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
        pub.subscribe(self.stop_listener, messages.STOP_ALL)
        pub.subscribe(self.set_shutter_speed, messages.SET_SHUTTER_SPEED)
        self.keepRunning=True

        self.set_shutter_speed(10)

    def run(self):
        folder = 'D:/star_guiding/images/2019-02-25.18-18-55'

        filenames = list(map(lambda s2: folder + '/' + s2, os.listdir(folder)))
        filenames = sorted(filenames, key = lambda s: int(s.split('/')[-1].split('.')[0]))

        filenames = filenames[:100]
        imgs = [None for file in filenames]

        count = 0
        while self.keepRunning:
            time.sleep(max(0.5, self.shutter_speed_ms / 1000.))

            index = count % len(imgs)
            if (count // len(imgs)) % 2 > 0: #flip around backwards for continuity
                index = len(imgs) - index - 1

            if imgs[index] is None:
                imgs[index] = load_image(filenames[index])

            img = imgs[index]
            count += 1

            img = img * self.shutter_speed_ms / BASE_SHUTTER_SPEED_MS
            pub.sendMessage(messages.NEW_IMAGE_FRAME, frame=img)

        
    def set_shutter_speed(self, new_speed_ms):
        self.shutter_speed_ms = new_speed_ms
    
    def stop_listener(self):
        self.keepRunning=False

def test():
    c = Camera()
    c.start()
    
    def test_get_image(frame):
            cv2.imshow("test image", frame)
            cv2.waitKey(1)
            
    pub.subscribe(test_get_image, messages.NEW_IMAGE_FRAME)
    
    time.sleep(10)
    
    pub.sendMessage(messages.STOP_ALL)

if __name__ == "__main__":
    test()
    