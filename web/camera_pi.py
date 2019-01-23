import io
import time
import picamera
from base_camera import BaseCamera
import numpy as np
import cv2

class Camera(BaseCamera):
    
    #@staticmethod
    #def set_shutter_speed(ms):
         
    @staticmethod
    def frames():
        count = 0
        with picamera.PiCamera() as camera:
            print('started picamera')
            
            #camera.resolution = (2592, 1952)
            camera.resolution = (672, 496)
            camera.shutter_speed = 10000
            
            # let camera warm up
            time.sleep(2)
            
            while 1:
                print(BaseCamera.settings_changed)
                if(BaseCamera.settings_changed):
                    camera.shutter_speed = BaseCamera.shutter_speed
                    
                    BaseCamera.settings_changed = False
                    
                #print(self.shutter_speed)
                image_rgb = np.empty((camera.resolution[1], camera.resolution[0], 3), dtype=np.uint8)
                camera.capture(image_rgb, 'rgb')
                image_bw = image_rgb[:, :, 0]
                
                ret, jpeg = cv2.imencode('.jpg', image_bw)
                yield jpeg.tobytes()
                
            
            """
            stream = io.BytesIO()
            for _ in camera.capture_continuous(stream, 'jpeg',
                                                 use_video_port=True):
                # return current frame
                stream.seek(0)
                print('new frame', count)
                count += 1
                yield stream.read()

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()
            """