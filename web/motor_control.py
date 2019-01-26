from gpiozero import LED
import time
import threading
from datetime import datetime

step_pin = 3
microstep_pin = 2

"""
dir = LED(2)
step = LED(3)
micro = LED(4)
led.on()
"""

def busy_sleep_us(us, offset_us = 34):
    start = datetime.now()
    
    while(1):
        now = datetime.now()
        delta = now - start
        us_elapsed = delta.seconds * 1000000 + delta.microseconds
        if us_elapsed + offset_us >= us:
            break
        
sleep_us = lambda us: time.sleep(us / 1E6)
#sleep_us = busy_sleep_us

class MotorControl(object):
    thread = None
    adjustment_factor = 1.0
    tracking_factor = 1.0
    _kill = False
    _movement_enabled = True
    _restart_movement = False
    
    def __init__(self):
        if MotorControl.thread is None:
            print('thread is none')
            MotorControl.thread = threading.Thread(target=self._thread)
            MotorControl.thread.start()
        else:
            print('thread isnt None')
            
    def kill(self):
        MotorControl._kill = True
        
    def enable_movement(self):
        MotorControl._restart_movement = True
        #MotorControl._movement_enabled = True
        
    def disable_movement(self):
        MotorControl._movement_enabled = False

    @classmethod
    def _thread(cls):
        #output_dir = LED(dir_pin)
        output_step = LED(step_pin)
        output_micro = LED(microstep_pin)
        
        #output_dir.off() #set the direction
        output_micro.on() #microstepping on
        
        degrees_per_second = 360. / (24 * 60 * 60)
        motor_step_size_degrees = 1.8 / 16.0 #with microsteps on
        gearbox_ratio = 99 + 1044. / 2057.
        worm_ratio = 27. * 84. / 52.
        output_step_size = motor_step_size_degrees / (gearbox_ratio * worm_ratio)
        steps_per_second = degrees_per_second / output_step_size
        calculated_delay_us = 1E6 / (2. * steps_per_second)
        print('calculated delay (us): ', calculated_delay_us)
        
        error_integral_us = 0
        
        current_delay_us = calculated_delay_us
        last_timestamp = datetime.now()
        sleep_us(current_delay_us); #just to start from having a big offset at the start
        i=0
        while(not MotorControl._kill):
            if MotorControl._movement_enabled:
                current_timestamp = datetime.now()
                delta = current_timestamp - last_timestamp
                elapsed_us = delta.seconds * 1E6 + delta.microseconds
                
                error_us = elapsed_us - current_delay_us
                error_integral_us += error_us
                
                if i % 1000 == 0: print(error_integral_us)
                
                current_delay_us = calculated_delay_us * MotorControl.adjustment_factor * MotorControl.tracking_factor
                
                current_delay_minus_error_us = current_delay_us - error_integral_us
                if current_delay_minus_error_us < 1000: current_delay_minus_error_us = 1000 #cant go <0, also need the stepper to move in time
                sleep_us(current_delay_minus_error_us)
                
                last_timestamp = current_timestamp
                output_step.value = not output_step.value
                
                i+=1
            elif MotorControl._restart_movement:
                i = 0
                error_integral_us
                last_timestamp = datetime.now()
                MotorControl._restart_movement = False
                MotorControl._movement_enabled = True
                sleep_us(current_delay_us)
            else:
                time.sleep(1)
            
            
if __name__ == "__main__":
    mc = MotorControl()
    print('after MotorControl()')
    time.sleep(30)
    mc.kill()
        