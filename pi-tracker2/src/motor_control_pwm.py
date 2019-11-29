import time
import threading
from datetime import datetime
import threading
import messages
import redis_helpers
import redis
import numpy as np

if 1:
    from gpiozero import LED, PWMLED
else:    
    class PWMLED(object):
        value = False
        frequency = 0
        def __init__(*args):
            pass

        def on(self):
            pass

        def off(self):
            pass

    class LED(object):
        def __init__(*args): pass
        def on(self): pass
        def off(self): pass
        

DIR_PIN_NUM = 14
STEP_PIN_NUM = 15
MICRO_STEP_PIN_NUM = 18

class MotorControl(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)

        self.dir_pin = LED(DIR_PIN_NUM)
        self.step_pin = PWMLED(STEP_PIN_NUM)
        self.micro_pin = LED(MICRO_STEP_PIN_NUM)

        self.dir_pin.on()
        self.micro_pin.on()

        self.step_pin.value = 0

        seconds_per_rotation = (24.*60.*60.)
        gear_ratio = (99 + 1044./ 2057.) * 27 * 84 / 52.
        steps_per_rotation = 200. * 16.
        self.base_steps_per_second = steps_per_rotation * gear_ratio / seconds_per_rotation 

        r = redis.StrictRedis(host='localhost', port=6379) 
        p = r.pubsub(ignore_subscribe_messages=True)
        self.kill = False
        p.subscribe(**{messages.STOP_ALL:self.stop_all_handler,
                #messages.CMD_ENABLE_AXIS_2_MOVEMENT:self.enable_movement_handler,
                #messages.CMD_DISABLE_AXIS_2_MOVEMENT:self.disable_movement_handler,
                messages.CMD_SET_SPEED_ADJUSTMENT_DEC:self.set_speed_handler,
            })

        self.thread = p.run_in_thread(sleep_time = 0.01)

    def stop_all_handler(self, message):
        self.kill = True

    def enable_movement_handler(self, message):
        print('movement enabled')
        self.movement_enabled = True

    def disable_movement_handler(self, message):
        self.movement_enabled = False
    
    def set_speed_handler(self, message):
        self.current_speed = redis_helpers.fromRedis(message['data'])
        print('orthogonal speed: ', self.current_speed)
        if self.current_speed < 0:
            self.dir_pin.off()
        else:
            self.dir_pin.on()
    
        if self.current_speed == 0:
            self.step_pin.value = 0
        else:   
            self.step_pin.value = 0.5
            if np.abs(self.current_speed) > 100:
                print('macro')
                self.micro_pin.off()
                self.step_pin.frequency = self.base_steps_per_second * np.abs(self.current_speed) / 16
            else:
                print('micro')
                self.micro_pin.on() 
                self.step_pin.frequency = self.base_steps_per_second * np.abs(self.current_speed)
            # print('frequency: ', self.step_pin.frequency)


    def run(self):

        #self.adjustment_factor = 1.0
        #self.tracking_factor = 1.0
        #self.ema_factor = 0.0
        self.movement_enabled = True
        #self.prev_speed_error = 0
        
        #steps_per_rotation = 400
        #gear_ratio = 128.
        #steps_per_rotation = 400.
        #self.base_steps_per_second = steps_per_rotation * gear_ratio / seconds_per_rotation 

        #print('baseline steps per second: ', self.base_steps_per_second)
        
        while not self.kill:
            if self.movement_enabled:
                pass
                #new_speed = self.base_steps_per_second * self.adjustment_factor 
                # print('new_speed: ', new_speed)
                # speed_float = dspin.dspin_SpdCalc(new_speed) - self.prev_speed_error
                # print(speed_float)
                #speed_int = int(np.round(speed_float))
                #print('speed: ', speed_int)
                #self.prev_speed_error = speed_int - speed_float
                #dspin.dspin_Run(dspin.FWD, speed_int)
		
            else:
                #dspin.dspin_SoftStop()
                pass

            time.sleep(0.5)

        self.thread.stop()

if __name__ == "__main__":
    r = redis.StrictRedis(host='localhost', port=6379) 

    mc = MotorControl()
    mc.start()
    print('started')
    time.sleep(5)

    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(10))

    time.sleep(5)

    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(0))

    time.sleep(5)

    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(-1000))
    time.sleep(5)

    r.publish(messages.STOP_ALL, "")
