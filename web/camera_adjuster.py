
import time
import threading
from datetime import datetime
import numpy as np

from motor_control import MotorControl

class CameraAdjuster(object):
    thread = None
    camera = None
    
    restartGuiding = False
    runGuiding = False
    
    def __init__(self, camera = None):
        if CameraAdjuster.thread is None:
            #print('thread is none')
            CameraAdjuster.thread = threading.Thread(target=self._thread, args = (camera,))
            CameraAdjuster.thread.start()
            
    def start_guiding(self):        
        print('start following')
        CameraAdjuster.restartGuiding = True
        
    def stop_guiding(self):
        print('stop following')
        CameraAdjuster.runGuiding = True
            
    @classmethod
    def _thread(cls, camera):
        desired_guide_location = None
        guide_vector = None
        seconds_for_vector = 10
        adjustment_target_seconds = 3
        mc = MotorControl()


        while(1):
            if CameraAdjuster.restartGuiding:
                print('(re)starting guiding process')
                start_time = datetime.now()

                mc.disable_movement()
                start_frame, start_shift = camera.get_frame()

                while (datetime.now() - start_time).seconds < seconds_for_vector:
                    frame, shift = camera.get_frame()
                    print(shift)

                end_time = datetime.now()

                mc.enable_movement()
                    
                guide_vector = np.array((shift[0] - start_shift[0], shift[1] - start_shift[1])) / (end_time - start_time).seconds
                desired_guide_location = shift

                print('guide vector (per second): ', guide_vector)
                CameraAdjuster.restartGuiding = False
                CameraAdjuster.runGuiding = True

            elif not CameraAdjuster.runGuiding:
                time.sleep(1)

            else:

                frame, shift_since_start = camera.get_frame()

                shift = np.array((shift_since_start[0] - desired_guide_location[0], shift_since_start[1] - desired_guide_location[1]))
                print(shift)

                distance_along_guide = np.dot(shift, guide_vector) / (np.linalg.norm(guide_vector)**2)
                print(distance_along_guide)

                orthogonal_vector = shift - distance_along_guide * guide_vector
                orthogonal_distance = np.linalg.norm(orthogonal_vector) 
                print('orthogonal: ', orthogonal_vector, orthogonal_distance)

                adjustment = distance_along_guide / adjustment_target_seconds 
                adjustment = np.clip(adjustment, -0.5, 0.5)
                
                new_speed_adjustment = 1.0 + adjustment

                print('adjustment: ', new_speed_adjustment)

                mc.set_tracking_factor(new_speed_adjustment)

                #guide
                pass