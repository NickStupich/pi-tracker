from picamera import mmal, mmalobj as mo
import time
import numpy as np
import cv2
from pubsub import pub
import messages
import threading

class Camera(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
        pub.subscribe(self.stop_listener, messages.STOP_ALL)
        pub.subscribe(self.set_shutter_speed, messages.SET_SHUTTER_SPEED)
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


        self.set_shutter_speed(10)

    def run(self):
        self.camera.outputs[0].enable(self.image_callback)
       
        while self.keepRunning:
            time.sleep(1)
        
        self.camera.outputs[0].disable()
        print('shut down camera')
        
    def set_shutter_speed(self, new_speed_ms):
        self.shutter_speed_ms = new_speed_ms
        self.camera.control.params[mmal.MMAL_PARAMETER_SHUTTER_SPEED] = new_speed_ms * 1000
        
    def image_callback(self, port, buf):
        #TODO: smoothing of multiple images. if needed?
        if len(buf.data) > 0:
            img = np.frombuffer(buf.data, dtype=np.uint8).reshape(1088, 1920, 3)
            bw_img = img[:, :, 1]
            
            pub.sendMessage(messages.NEW_IMAGE_FRAME, frame=bw_img)

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
            
    pub.subscribe(test_get_image, messages.NEW_IMAGE_FRAME)
    
    time.sleep(10)
    
    pub.sendMessage(messages.STOP_ALL)

if __name__ == "__main__":
    test()
    