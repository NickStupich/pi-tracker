import time
import threading
from datetime import datetime
import threading
import messages
import redis_helpers
import redis

# import dspin_l6470 as dspin
import dspin_fake as dspin

class MotorControl(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        r = redis.StrictRedis(host='localhost', port=6379) 
        p = r.pubsub(ignore_subscribe_messages=True)
        self.kill = False
        p.subscribe(**{messages.STOP_ALL:self.stop_all_handler,

            })

        self.thread = p.run_in_thread(sleep_time = 0.01)

    def stop_all_handler(self, message):
        self.kill = True

    def run(self):

        self.adjustment_factor = 1.0
        self.tracking_factor = 1.0
        self.smoothed_tracking_factor = 1.0
        self.ema_factor = 0.0
        self.movement_enabled = True

        dspin.connect_l6470()
        seconds_per_rotation = (24.*60.*60.)
        gear_ratio = 128.
        steps_per_rotation = 400.
        self.base_steps_per_second = steps_per_rotation * gear_ratio / seconds_per_rotation 

        print('baseline steps per second: ', self.base_steps_per_second)
        
        while not self.kill:
            if self.movement_enabled:
                
                new_speed = self.base_steps_per_second / (self.adjustment_factor * self.smoothed_tracking_factor)
                # print('new_speed: ', new_speed)
                dspin.dspin_Run(dspin.FWD, dspin.dspin_SpdCalc(new_speed))
		
            else:
                dspin.SoftStop()

            time.sleep(1.0)

        dspin.disconnect_l6470()
        self.thread.stop()

if __name__ == "__main__":
    #dspin.connect_l6470()
    #dspin.dspin_Run(dspin.FWD, 1000)
    #time.sleep(3)
    #dspin.disconnect_l6470()

    mc = MotorControl()
    mc.start()
    print('after MotorControl()')
    time.sleep(10)

    r = redis.StrictRedis(host='localhost', port=6379) 
    r.publish(messages.STOP_ALL, "")