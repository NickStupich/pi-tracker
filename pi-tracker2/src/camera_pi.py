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

class Camera(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
        self.keepRunning=True
        
        camera = mo.MMALCamera()
        
        camera.outputs[0].framesize = (1920, 1080)
        camera.outputs[0].framerate = 2
        camera.outputs[0].format = mmal.MMAL_ENCODING_RGB24

        camera.control.params[mmal.MMAL_PARAMETER_ISO] = 800
        
        awb = camera.control.params[mmal.MMAL_PARAMETER_AWB_MODE]
        awb.value = mmal.MMAL_PARAM_AWBMODE_SUNLIGHT
        camera.control.params[mmal.MMAL_PARAMETER_AWB_MODE] = awb
        
        camera.outputs[0].commit()
        
        self.camera = camera


        self.set_shutter_speed(100)
                
        p = r.pubsub(ignore_subscribe_messages=True)

        def stop_all_handler(message):
            print('got stop_all message')
            self.keepRunning = False
        p.subscribe(**{messages.STOP_ALL:stop_all_handler})

        self.thread = p.run_in_thread(sleep_time = 0.01)


    def run(self):
        self.camera.outputs[0].enable(self.image_callback)
       
        while self.keepRunning:
            time.sleep(1)
        
        self.camera.outputs[0].disable()
        print('shut down camera')
        
        self.thread.stop()
        
    def set_shutter_speed(self, new_speed_ms):
        self.shutter_speed_ms = new_speed_ms
        self.camera.control.params[mmal.MMAL_PARAMETER_SHUTTER_SPEED] = new_speed_ms * 1000
        
    def image_callback(self, port, buf):
        #TODO: smoothing of multiple images. if needed?
        if len(buf.data) > 0:
            img = np.frombuffer(buf.data, dtype=np.uint8).reshape(1088, 1920, 3)
            bw_img = img[:, :, 1]
            
            # pub.sendMessage(messages.NEW_IMAGE_FRAME, frame=bw_img)
            #r.publish(messages.NEW_IMAGE_FRAME, bw_img)
            
            r.publish(messages.NEW_IMAGE_FRAME, redis_helpers.toRedis(bw_img))
            #if filtered_image is None:
            #    filtered_image = bw_img.copy()
            #else:
                #filtered_image = filtered_image * ema + bw_img 
            #    filtered_image = bw_img.copy()
            #cv2.imshow('image', img)
            #cv2.imshow('image', filtered_image)
            #cv2.imshow('image', bw_img)
            #cv2.waitKey(1)

        return False
    
    def stop_listener(self):
        self.keepRunning=False

def test():
    c = Camera()
    c.start()
    
    def test_get_image(frame):
            cv2.imshow("test image", frame)
            cv2.waitKey(1)
            
    # pub.subscribe(test_get_image, messages.NEW_IMAGE_FRAME)
    p = r.pubsub()
    start = datetime.datetime.now()
    p.subscribe(messages.NEW_IMAGE_FRAME)

    while (datetime.datetime.now() - start).total_seconds() < 10:
        # print((datetime.datetime.now() - start).total_seconds())
        message = p.get_message()
        if message:
            # print(message)
            channel = message['channel']
            data = message['data']
            msg_type = message['type']
            print(channel, msg_type)
            if 'message' in msg_type:
                img = redis_helpers.fromRedis(data, np.uint8)
                print(img.shape)

                test_get_image(img)
            # print(dir(message))

        time.sleep(0.1)

    # time.sleep(10)
    
    r.publish(messages.STOP_ALL, "")

if __name__ == "__main__":
    test()
    