import time
import threading
from datetime import datetime
import threading
import messages
import redis_helpers
import redis
import numpy as np

import dspin_l6470

class MotorControl(threading.Thread):
    
    def __init__(self, 
                bus, cs_pin, slave_pin, reset_pin, 
                speed_adjustment_msg,
                base_steps_per_second,
                default_speed #1 for ra, 0 for dec
                ):
        threading.Thread.__init__(self)

        self.dspin = dspin_l6470.Dspin_motor(bus, cs_pin, slave_pin, reset_pin)
        self.base_steps_per_second = base_steps_per_second
        self.default_speed = default_speed

        r = redis.StrictRedis(host='localhost', port=6379) 
        p = r.pubsub(ignore_subscribe_messages=True)
        self.kill = False
        p.subscribe(**{messages.STOP_ALL:self.stop_all_handler,
                messages.CMD_ENABLE_MOVEMENT:self.enable_movement_handler,
                messages.CMD_DISABLE_MOVEMENT:self.disable_movement_handler,
                speed_adjustment_msg:self.set_adjustment_factor_handler,
            })

        self.thread = p.run_in_thread(sleep_time = 0.01)

    def stop_all_handler(self, message):
        self.kill = True

    def enable_movement_handler(self, message):
        print('movement enabled')
        self.movement_enabled = True

    def disable_movement_handler(self, message):
        self.movement_enabled = False
    
    def set_adjustment_factor_handler(self, message):
        self.adjustment_factor = redis_helpers.fromRedis(message['data'])

    def run(self):

        self.adjustment_factor = 0.0
        self.movement_enabled = True
        self.prev_speed_error = 0

        self.dspin.connect_l6470()

        #print('baseline steps per second: ', self.base_steps_per_second)
        
        while not self.kill:
            if self.movement_enabled:
                
                new_speed = self.base_steps_per_second * (self.default_speed + self.adjustment_factor )
                new_speed_abs = np.abs(new_speed)
                # print('new_speed: ', new_speed)
                speed_float = self.dspin.dspin_SpdCalc(new_speed_abs) - self.prev_speed_error
                # print(speed_float)
                speed_int = int(np.round(speed_float))
                self.prev_speed_error = speed_int - speed_float
                direction = dspin_l6470.FWD if new_speed > 0 else dspin_l6470.REV
                
                # print('speed, dir: ', speed_int, direction)
                self.dspin.dspin_Run(direction, speed_int)
		
            else:
                self.dspin.dspin_SoftStop()

            time.sleep(0.5)

        self.dspin.disconnect_l6470()
        self.thread.stop()

if __name__ == "__main__":
    r = redis.StrictRedis(host='localhost', port=6379) 

    seconds_per_rotation = (24.*60.*60.)
    gear_ratio = 128.
    steps_per_rotation = 400.
    base_steps_per_second = steps_per_rotation * gear_ratio / seconds_per_rotation  
    mc_ra = MotorControl(bus=0, cs_pin = 0, slave_pin=25, reset_pin = 3, 
            speed_adjustment_msg = messages.CMD_SET_SPEED_ADJUSTMENT_RA,
            base_steps_per_second = base_steps_per_second,
            default_speed = 1,)    
    mc_ra.start()

    print('after MotorControl()')
    time.sleep(3)

    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(1.2))

    time.sleep(3)

    r.publish(messages.CMD_DISABLE_MOVEMENT, "")

    time.sleep(3)

    r.publish(messages.CMD_ENABLE_MOVEMENT, "")

    time.sleep(3)

    r.publish(messages.STOP_ALL, "")
