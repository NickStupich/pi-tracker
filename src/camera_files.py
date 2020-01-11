import time
import numpy as np
import cv2
import messages
import threading
import os
import redis
import datetime
import redis_helpers

BASE_SHUTTER_SPEED_MS = 100
r = redis.StrictRedis(host='localhost', port=6379) 

def load_image(filename):
    result = cv2.imread(filename, 0)
    return result

class Camera(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        p = r.pubsub(ignore_subscribe_messages=True)

        self.keepRunning=True
        self.set_shutter_speed(100)

        def stop_all_handler(message):
            print('got stop_all message')
            self.keepRunning = False
        p.subscribe(**{messages.STOP_ALL:stop_all_handler})

        self.thread = p.run_in_thread(sleep_time = 0.01)

    def run(self):
        # folder = 'D:/star_guiding/images/2019-02-25.18-18-55'
        folder = '../test/images-2019-02-25.18-11-26'

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

            img = img * int(self.shutter_speed_ms / BASE_SHUTTER_SPEED_MS)
            r.publish(messages.NEW_IMAGE_FRAME, redis_helpers.toRedis(img))

            max_value = np.max(img)
            r.publish(messages.STATUS_MAX_PIXEL_VALUE, redis_helpers.toRedis(max_value))

        self.thread.stop()
        
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
            
    p = r.pubsub(ignore_subscribe_messages=True)
    start = datetime.datetime.now()
    p.subscribe(messages.NEW_IMAGE_FRAME)

    while (datetime.datetime.now() - start).total_seconds() < 10:
        message = p.get_message()
        if message:
            channel = message['channel']
            data = message['data']
            msg_type = message['type']

            img = redis_helpers.fromRedis(data, np.uint8)

            test_get_image(img)

        time.sleep(0.1)

    r.publish(messages.STOP_ALL, "")

if __name__ == "__main__":
    test()
    