from picamera import mmal, mmalobj as mo
import time
import numpy as np
import cv2
import redis
import messages
import threading
import datetime
import redis
import redis_helpers

r = redis.StrictRedis(host='localhost', port=6379) 

PIXEL_SIZE_IN_ARC_SECONDS = 4.17

class Camera(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
        self.keepRunning=True
        
        camera = mo.MMALCamera()
        
        camera.outputs[0].framesize = (1920, 1080)
        camera.outputs[0].framerate = 1
        camera.outputs[0].format = mmal.MMAL_ENCODING_RGB24

        camera.control.params[mmal.MMAL_PARAMETER_ISO] = 800
        
        awb = camera.control.params[mmal.MMAL_PARAMETER_AWB_MODE]
        awb.value = mmal.MMAL_PARAM_AWBMODE_SUNLIGHT
        camera.control.params[mmal.MMAL_PARAMETER_AWB_MODE] = awb
        
        camera.outputs[0].commit()
        
        self.camera = camera

        self.set_shutter_speed(300)
                
        p = r.pubsub(ignore_subscribe_messages=True)

        p.subscribe(**{messages.STOP_ALL:self.stop_all_handler,
                        messages.CMD_SET_SHUTTER_SPEED : self.set_shutter_speed_handler})

        self.thread = p.run_in_thread(sleep_time = 0.01)


    def run(self):
        self.camera.outputs[0].enable(self.image_callback)
       
        while self.keepRunning:
            time.sleep(1)
        
        self.camera.outputs[0].disable()
        print('shut down camera')
        
        self.thread.stop()

    def stop_all_handler(self, message):
        print('got stop_all message')
        self.keepRunning = False
       
    def set_shutter_speed(self, new_speed_ms):
        self.camera.control.params[mmal.MMAL_PARAMETER_SHUTTER_SPEED] = new_speed_ms * 1000
        self.shutter_speed_ms = new_speed_ms

    def set_shutter_speed_handler(self, message):
        shutter_speed_ms = redis_helpers.fromRedis(message['data'])
        self.set_shutter_speed(shutter_speed_ms)
        
    def image_callback(self, port, buf):
        #TODO: smoothing of multiple images. if needed?
        if len(buf.data) > 0:
            img = np.frombuffer(buf.data, dtype=np.uint8).reshape(1088, 1920, 3)

            #TODO: average?
            bw_img = img[:, :, 1]
            
            r.publish(messages.NEW_IMAGE_FRAME, redis_helpers.toRedis(bw_img))

            max_value = np.max(bw_img)
            r.publish(messages.STATUS_MAX_PIXEL_VALUE, redis_helpers.toRedis(max_value))

        return False
    
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
    
