
import time
import threading
from datetime import datetime

try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident

step_pin = 3
microstep_pin = 2


import is_pi

if is_pi.is_pi:
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
        

class MotorEvent(object):
    """An Event-like class that signals all active clients when a new frame is
    available.
    """
    def __init__(self):
        self.events = {}

    def wait(self, timeout = None):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait(timeout)

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()

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

        output_step = PWMLED(step_pin)
        output_micro = LED(microstep_pin)
        
        output_micro.on() #microstepping on
        
        degrees_per_second = 360. / (24 * 60 * 60)
        motor_step_size_degrees = 1.8 / 16.0 #with microsteps on
        gearbox_ratio = 99 + 1044. / 2057.
        worm_ratio = 27. * 84. / 52.
        output_step_size = motor_step_size_degrees / (gearbox_ratio * worm_ratio)
        steps_per_second = degrees_per_second / output_step_size
        print('steps per second: ', steps_per_second)
        
        while(not MotorControl._kill):
            print('updating...')
            if MotorControl._movement_enabled:
                
                frequency = steps_per_second / (MotorControl.adjustment_factor * MotorControl.smoothed_tracking_factor)
                print('frequency: ', frequency)
                output_step.value = 0.5
                output_step.frequency = frequency
            else:
                output_step.value = 0
                
            MotorControl.event.wait()
            MotorControl.event.clear()
            
            
if __name__ == "__main__":
    mc = MotorControl()
    print('after MotorControl()')
    time.sleep(10)

    mc.set_tracking_factor(0.5)
    time.sleep(5)
    mc.set_tracking_factor(2.0)
    time.sleep(5)
    mc.kill()
    
        

