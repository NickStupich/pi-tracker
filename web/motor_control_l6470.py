import time
import threading
from datetime import datetime

import dspin_l6470 as dspin
#from motor_control_pwm import MotorEvent
from motor_event import MotorEvent

class MotorControl(object):
    thread = None
    adjustment_factor = 1.0
    tracking_factor = 1.0
    smoothed_tracking_factor = 1.0
    ema_factor = 0.0
    _kill = False
    _movement_enabled = True
    _restart_movement = False
    event = MotorEvent()
    
    def __init__(self):
        if MotorControl.thread is None:
            MotorControl.thread = threading.Thread(target=self._thread)
            MotorControl.thread.start()
            
    def kill(self):
        dspin.disconnect_l6470()
        MotorControl._kill = True
        MotorControl.event.set()
        
    def enable_movement(self):
        MotorControl._movement_enabled = True
        MotorControl.event.set()
        
    def disable_movement(self):
        MotorControl._movement_enabled = False
        MotorControl.event.set()

    def set_tracking_factor(self, factor):
        MotorControl.tracking_factor = factor
        MotorControl.smoothed_tracking_factor = MotorControl.smoothed_tracking_factor * MotorControl.ema_factor + factor * (1 - MotorControl.ema_factor)
        MotorControl.event.set()

    def set_ema_factor(self, ema):
        MotorControl.ema_factor = ema
        # print('new ema factor: ', ema)

    @classmethod
    def _thread(cls):

        dspin.connect_l6470()
        seconds_per_rotation = (24.*60.*60.)
        gear_ratio = 128.
        steps_per_rotation = 400.
        steps_per_second = steps_per_rotation * gear_ratio / seconds_per_rotation 

        print('steps per second: ', steps_per_second)
        
        while(not MotorControl._kill):
            print('updating...')
            if MotorControl._movement_enabled:
                
                new_speed = steps_per_second / (MotorControl.adjustment_factor * MotorControl.smoothed_tracking_factor)
                print('new_speed: ', new_speed)
                dspin.dspin_Run(dspin.FWD, dspin.dspin_SpdCalc(new_speed))
		
            else:
                dspin.SoftStop()
                
            MotorControl.event.wait()
            MotorControl.event.clear()

if __name__ == "__main__":
	#dspin.connect_l6470()
	#dspin.dspin_Run(dspin.FWD, 1000)
	#time.sleep(3)
	#dspin.disconnect_l6470()

	mc = MotorControl()
	print('after MotorControl()')
	time.sleep(10)
	
	mc.set_tracking_factor(0.5)
	time.sleep(5)
	mc.set_tracking_factor(2.0)
	time.sleep(5)
	mc.kill()
