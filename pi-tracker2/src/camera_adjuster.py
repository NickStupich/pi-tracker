
import time
import threading
from datetime import datetime
import numpy as np

import messages

import redis
import redis_helpers

#TODO: longer after testing?
VECTOR_ESTIMATION_TIME_SECONDS = 10
ADJUSTMENT_TARGET_SECONDS = 3 #how 'aggressive' to pull towards ideal spot

class AdjusterStates:
    NOT_GUIDING = 0
    CMD_START_GUIDING = NOT_GUIDING +1
    START_GUIDING_DIR_1 = CMD_START_GUIDING + 1
    START_GUIDING_DIR_2 = START_GUIDING_DIR_1 + 1
    GUIDING = START_GUIDING_DIR_2 + 1

class CameraAdjuster(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        r = redis.StrictRedis(host='localhost', port=6379) 
        p = r.pubsub(ignore_subscribe_messages=True)
        self.kill = False
        p.subscribe(**{messages.STOP_ALL:self.stop_all_handler})
        self.thread = p.run_in_thread(sleep_time = 0.1)
            
    def stop_all_handler(self, message):
        self.kill = True
        self.thread.stop()

    def run(self):
        desired_location = None
        guide_vector = None

        orthogonal_distance = None
        parallel_distance = None
        update_time = None

        current_state = AdjusterStates.NOT_GUIDING

        r = redis.StrictRedis(host='localhost', port=6379) 
        p = r.pubsub(ignore_subscribe_messages=True)
        
        p.subscribe(messages.CMD_START_GUIDING)
        p.subscribe(messages.CMD_STOP_GUIDING) 
        p.subscribe(messages.STATUS_CURRENT_TRACKING_POSITION)

        start_guiding_dir_1_start_time = None
        start_guiding_dir_1_start_location = None

        guiding_dir_2_start_time = None
        
        while not self.kill:
            message = p.get_message()
            if message:
                channel = message['channel'].decode('ASCII')
                data = message['data']

                if channel == messages.CMD_START_GUIDING:
                    print('start guiding received')
                    desired_location = None #will get grabbed first
                    current_state = AdjusterStates.CMD_START_GUIDING

                    #TODO: publish state?

                elif channel == messages.CMD_STOP_GUIDING:
                    current_state = AdjusterStates.NOT_GUIDING
                    r.publish(messages.CMD_ENABLE_MOVEMENT, "")
                    r.publish(emssages.CMD_SET_ADJUSTMENT_FACTOR, redis_helpers.toRedis(1))
                    #publish state?

                elif channel == messages.STATUS_CURRENT_TRACKING_POSITION:
                    current_position = redis_helpers.fromRedis(data)
                    if current_state == AdjusterStates.NOT_GUIDING:
                        pass

                    elif current_state == AdjusterStates.CMD_START_GUIDING: #set up to calc guiding vector
                        r.publish(messages.CMD_DISABLE_MOVEMENT, "")
                        desired_location = current_position
                        #TODO: wait a frame or two?

                        start_guiding_dir_1_start_location = None
                        start_guiding_dir_1_start_time = None
                        current_state = AdjusterStates.START_GUIDING_DIR_1

                    elif current_state == AdjusterStates.START_GUIDING_DIR_1:   #calculate the guiding vector

                        if start_guiding_dir_1_start_location is None:
                            start_guiding_dir_1_start_time = datetime.now()
                            start_guiding_dir_1_start_location = current_position
                        elif (datetime.now() - start_guiding_dir_1_start_time).total_seconds() < VECTOR_ESTIMATION_TIME_SECONDS:
                            print('elapsed time: ', (datetime.now() - start_guiding_dir_1_start_time).total_seconds())
                        else: #end of guide vector finding in direction 1
                            start_guiding_dir_1_end_time = datetime.now()
                            start_guiding_dir_1_end_location = current_position


                            guide_vector = np.array((start_guiding_dir_1_end_location[0] - start_guiding_dir_1_start_location[0], 
                                                    start_guiding_dir_1_end_location[1] - start_guiding_dir_1_start_location[1])) / \
                                                            (start_guiding_dir_1_end_time - start_guiding_dir_1_start_time).total_seconds()

                            print('guide vector: ', guide_vector)

                            #now speed forwards to get back to original position
                            r.publish(messages.CMD_ENABLE_MOVEMENT, "")                                    
                            r.publish(messages.CMD_SET_ADJUSTMENT_FACTOR, redis_helpers.toRedis(2.0))
                            current_state = AdjusterStates.START_GUIDING_DIR_2


                    elif current_state == AdjusterStates.START_GUIDING_DIR_2:   #return to starting point, get off-axis vector
                        if guiding_dir_2_start_time is None:
                            guiding_dir_2_start_time = datetime.now()
    
                        shift = current_position - desired_location
                        distance_along_guide = np.dot(shift, guide_vector) / (np.linalg.norm(guide_vector)**2)

                        if distance_along_guide > 0:
                            #still getting back to the start
                            pass
                        else:        
                            elapsed_time_seconds = (datetime.now() - guiding_dir_2_start_time).total_seconds()
                            orthogonal_vector = (shift - distance_along_guide * guide_vector) / elapsed_time_seconds
                            print('orthogonal vector: ', orthogonal_vector)
                            #convert pixels/second to arc-seconds/s or something
                            orthogonal_distance = np.linalg.norm(orthogonal_vector) 


                            r.publish(messages.CMD_SET_ADJUSTMENT_FACTOR, redis_helpers.toRedis(1.0))
                            current_state = AdjusterStates.GUIDING
                            print('guiding...')

                    elif current_state == AdjusterStates.GUIDING:
                        shift = current_position - desired_location
                        distance_along_guide = np.dot(shift, guide_vector) / (np.linalg.norm(guide_vector)**2)
                        
                        parallel_distance = distance_along_guide
                        orthogonal_vector = shift - distance_along_guide * guide_vector
                        orthogonal_distance = np.linalg.norm(orthogonal_vector) 
                        
                        adjustment = distance_along_guide / ADJUSTMENT_TARGET_SECONDS 
                        adjustment = np.clip(adjustment, -0.5, 0.5)
                        
                        new_speed_adjustment = 1.0 - adjustment
                        
                        r.publish(messages.CMD_SET_ADJUSTMENT_FACTOR, redis_helpers.toRedis(new_speed_adjustment))

                    else:
                        print('unknown state: ', current_state)





if __name__ == "__main__":
    adjuster = CameraAdjuster()
    adjuster.start()
    time.sleep(2)

    r = redis.StrictRedis(host='localhost', port=6379) 

    r.publish(messages.CMD_START_GUIDING, "")
    time.sleep(VECTOR_ESTIMATION_TIME_SECONDS * 3)

    r.publish(messages.STOP_ALL, "")