import io
import time
import picamera
from base_camera import BaseCamera
import numpy as np
import cv2
import os
from datetime import datetime

class Camera(BaseCamera):
    images_directory = None
    
    @staticmethod
    def frames():
        count = 0
        with picamera.PiCamera() as camera:
            print('started picamera')

            update_cam_params(BaseCamera, camera)
            # let camera warm up
            time.sleep(2)
            
            while 1:
                if(BaseCamera.settings_changed):
                    update_cam_params(BaseCamera, camera)
                    BaseCamera.settings_changed = False
                    
                image_rgb = np.empty((camera.resolution[1], camera.resolution[0], 3), dtype=np.uint8)


                image_rgb = np.empty((1232, 1664, 3), dtype=np.uint8)
                
                camera.capture(image_rgb, 'rgb')
                if 1:
                    image_bw_full = np.copy(image_rgb[:1232, :1640, 0])
                    image_reshaped = np.reshape(image_bw_full, (image_bw_full.shape[0]//2, 2, image_bw_full.shape[1]//2, 2))
                    image_bw = np.mean(image_reshaped, axis=(1, 3)).astype(image_reshaped.dtype)                
                
                if BaseCamera.save_images:
                    if images_directory is None:
                        images_directory = os.path.join('/home/pi/projects/pi-tracker/web/images', datetime.now().strftime("%Y-%m-%d.%H:%M:%S"))
                        os.mkdir(images_directory)
                        
                    filename = os.path.join(images_directory, '%s.jpg' % count)
                    cv2.imwrite(filename, image_bw)

                else:
                    images_directory = None #force to make a new folder next time
                
                
                count += 1
                yield image_bw
                
            
def update_cam_params(BaseCamera, camera):
    print('setting camera parameters')
    camera.resolution = 1640, 1232
    camera.framerate = min(10, 1000 // BaseCamera.shutter_speed_ms)
    camera.shutter_speed = BaseCamera.shutter_speed_ms * 1000
