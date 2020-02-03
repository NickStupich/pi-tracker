
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
ORTHOGONAL_ADJUSTMENT_TARGET_SECONDS = 10
MAX_ADJUSTMENT = 1
GUIDE_CAM_ARC_SECONDS_PER_PIXEL = 4.1 #??

def angle_between_vectors(v1, v2):
    return np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))) * 180 / np.pi

class AdjusterStates:
    NOT_GUIDING = 0
    CMD_START_GUIDING = NOT_GUIDING +1
    START_GUIDING_DIR_1 = CMD_START_GUIDING + 1
    START_GUIDING_DIR_2 = START_GUIDING_DIR_1 + 1
    
    START_GUIDING_DIR_ORTH_1 = START_GUIDING_DIR_2 + 1
    START_GUIDING_DIR_ORTH_2 = START_GUIDING_DIR_ORTH_1 + 1

    GUIDING = START_GUIDING_DIR_ORTH_2 + 1

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
        guide_vector_orthogonal = None

        orthogonal_distance = None
        parallel_distance = None
        update_time = None

        filtered_adjustment = 0
        ema_factor = 0.8        

        current_state = AdjusterStates.NOT_GUIDING

        r = redis.StrictRedis(host='localhost', port=6379) 
        p = r.pubsub(ignore_subscribe_messages=True)
        
        p.subscribe(messages.CMD_START_GUIDING)
        p.subscribe(messages.CMD_STOP_GUIDING) 
        p.subscribe(messages.STATUS_CURRENT_TRACKING_POSITION)
        p.subscribe(messages.CMD_START_TRACKING)
        p.subscribe(messages.STATUS_STARTING_TRACKING_POSITION)
        p.subscribe(messages.CMD_SET_DITHERING_POSITION_OFFSET_PIXELS)
        p.subscribe(messages.STATUS_GET_ALL_STATUS)

        start_guiding_dir_1_start_time = None
        start_guiding_dir_1_start_location = None

        guiding_dir_2_start_time = None

        guiding_dir_orth_start_time = None

        failed_track_count = 0

        dithering_offset = [0, 0]
        
        while not self.kill:
            message = p.get_message()
            if message:
                channel = message['channel'].decode('ASCII')
                data = message['data']

                if channel == messages.CMD_START_TRACKING:
                    #reset things
                    desired_location = None

                elif channel == messages.CMD_START_GUIDING:
                    print('start guiding received')
                    #desired_location = None #will get grabbed first
                    current_state = AdjusterStates.CMD_START_GUIDING

                    #TODO: publish state?

                elif channel == messages.CMD_STOP_GUIDING:
                    r.publish(messages.CMD_ENABLE_MOVEMENT, "") #in case this came in during guide vector finding
                    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(0))
                    r.publish(messages.STATUS_CURRENT_RAW_ADJUSTMENT, redis_helpers.toRedis(0))
                    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(0))

                    current_state = AdjusterStates.NOT_GUIDING
                    desired_location = None 
                    #publish state?

                elif channel == messages.STATUS_STARTING_TRACKING_POSITION:
                    desired_location = redis_helpers.fromRedis(data)
                    print('adjuster got new desired location: ', desired_location)

                elif channel == messages.CMD_SET_DITHERING_POSITION_OFFSET_PIXELS:
                    dithering_offset = redis_helpers.fromRedis(data)
                    # print('new dithering offset: ', dithering_offset)

                elif channel == messages.STATUS_GET_ALL_STATUS:
                    r.publish(messages.STATUS_GUIDING_STATUS, redis_helpers.toRedis(current_state != AdjusterStates.NOT_GUIDING))

                elif channel == messages.STATUS_CURRENT_TRACKING_POSITION:
                    current_position = redis_helpers.fromRedis(data)

                    if desired_location is None:
                        print('trying to track with no desired location?')
                        #desired_location = current_position
                        continue
                    else:
                        shift = current_position - desired_location
                        r.publish(messages.STATUS_DRIFT_X, redis_helpers.toRedis(shift[1]))
                        r.publish(messages.STATUS_DRIFT_Y, redis_helpers.toRedis(shift[0]))

                    if current_state == AdjusterStates.NOT_GUIDING:
                        pass

                    elif current_state == AdjusterStates.CMD_START_GUIDING: #set up to calc guiding vector
                        r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(-1))

                        #desired_location = current_position
                        #TODO: wait a frame or two?

                        start_guiding_dir_1_start_location = None
                        start_guiding_dir_1_start_time = None
                        current_state = AdjusterStates.START_GUIDING_DIR_1

                    elif current_state == AdjusterStates.START_GUIDING_DIR_1:   #calculate the guiding vector

                        if start_guiding_dir_1_start_location is None:
                            start_guiding_dir_1_start_time = datetime.now()
                            start_guiding_dir_1_start_location = current_position
                        elif (datetime.now() - start_guiding_dir_1_start_time).total_seconds() < VECTOR_ESTIMATION_TIME_SECONDS:
                            pass
                        else: #end of guide vector finding in direction 1
                            start_guiding_dir_1_end_time = datetime.now()
                            start_guiding_dir_1_end_location = current_position


                            guide_vector = np.array((start_guiding_dir_1_end_location[0] - start_guiding_dir_1_start_location[0], 
                                                    start_guiding_dir_1_end_location[1] - start_guiding_dir_1_start_location[1])) / \
                                                            (start_guiding_dir_1_end_time - start_guiding_dir_1_start_time).total_seconds()

                            print('guide vector: ', guide_vector)
                            r.publish(messages.STATUS_GUIDE_VECTOR_RA, redis_helpers.toRedis(guide_vector))

                            #now speed forwards to get back to original position
                            # r.publish(messages.CMD_ENABLE_MOVEMENT, "")                                    
                            r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(1.0))
                            current_state = AdjusterStates.START_GUIDING_DIR_2

                    elif current_state == AdjusterStates.START_GUIDING_DIR_2:   #return to starting point, get off-axis vector
                        
                        if guiding_dir_2_start_time is None:
                            guiding_dir_2_start_time = datetime.now()
                        else:
        
                            distance_along_guide = np.dot(shift, guide_vector) / (np.linalg.norm(guide_vector)**2)
                            print('guide state 2, distance along guide: ', distance_along_guide)
                            if distance_along_guide > 0:
                                #still getting back to the start
                                pass
                            else:        
                                # elapsed_time_seconds = (datetime.now() - guiding_dir_2_start_time).total_seconds()
                                
                                calibration_time_seconds = (datetime.now() - start_guiding_dir_1_start_time).total_seconds()
                                shift = current_position - desired_location
                                orthogonal_distance_entire_calibration_pixels = np.dot(shift, [-guide_vector[1], guide_vector[0]])

                                calibration_process_orthogonal_drift = orthogonal_distance_entire_calibration_pixels * GUIDE_CAM_ARC_SECONDS_PER_PIXEL / calibration_time_seconds

                                # orthogonal_vector = (shift - distance_along_guide * guide_vector) / elapsed_time_seconds
                                # print('orthogonal vector: ', orthogonal_vector)
                                # #convert pixels/second to arc-seconds/s or something
                                # orthogonal_distance = np.linalg.norm(orthogonal_vector) 

                                r.publish(messages.STATUS_CALIBRATION_DRIFT_ARC_SECONDS, redis_helpers.toRedis(calibration_process_orthogonal_drift))

                                r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(0.))
                                filtered_adjustment = 0 #reset
                                current_state = AdjusterStates.START_GUIDING_DIR_ORTH_1
                                guiding_dir_orth_start_time = None
                                print('guiding...')

                    elif current_state in [AdjusterStates.START_GUIDING_DIR_ORTH_1, AdjusterStates.START_GUIDING_DIR_ORTH_2,
                        AdjusterStates.GUIDING]:

                        if current_position is None:
                            failed_track_count += 1

                            if failed_track_count > 20:
                                print('failed tracking too many times, trying to restart...?')
                                # r.publish(messages.CMD_START_TRACKING, "")
                                # r.publish(messages.CMD_STOP_GUIDING)
                                # r.publish(messages.CMD_START_GUIDING)

                                current_state = AdjusterStates.NOT_GUIDING
                                filtered_adjustment_ra = 0
                                raw_adjustment_ra = 0
                                parallel_distance = 0
                                orthogonal_distance = 0
                                filtered_adjustment_dec = 0
                                raw_adjustment_dec = 0

                                r.publish(messages.STATUS_FAILED_TRACKING_COUNT, redis_helpers.toRedis(failed_track_count))
                        else:
                            failed_track_count = 0
                            r.publish(messages.STATUS_FAILED_TRACKING_COUNT, redis_helpers.toRedis(failed_track_count))

                            #do parallel guiding in all states. only dither once we're up and running
                            if current_state == AdjusterStates.GUIDING:
                                shift = current_position - (desired_location + dithering_offset)
                            else:
                                shift = current_position - desired_location
                            # print('shift: ', shift)
                            parallel_distance = np.dot(shift, guide_vector) / (np.linalg.norm(guide_vector)**2)
                        
                            if guide_vector_orthogonal is None:
                                orthogonal_distance = 0
                            else:   
                                orthogonal_distance = np.dot(shift, guide_vector_orthogonal) / (np.linalg.norm(guide_vector_orthogonal)**2)
                            
                            raw_adjustment_ra = parallel_distance / ADJUSTMENT_TARGET_SECONDS 
                            clipped_adjustment = np.clip(raw_adjustment_ra, -MAX_ADJUSTMENT, MAX_ADJUSTMENT)
                            filtered_adjustment = filtered_adjustment * ema_factor + clipped_adjustment * (1 - ema_factor)
                            filtered_adjustment_ra = filtered_adjustment

                            if current_state == AdjusterStates.START_GUIDING_DIR_ORTH_1:                                
                                if guiding_dir_orth_start_time is None:
                                    print('starting guiding for orthogonal')
                                    guiding_dir_orth_start_time = datetime.now()
                                    guiding_dir_orth_start_location = current_position
                                    filtered_adjustment_dec = -1
                                    raw_adjustment_dec = -1
                                else:
                                    elapsed_time_seconds = (datetime.now() - guiding_dir_orth_start_time).total_seconds()
                                    print('orth guide vector estimating time: ', elapsed_time_seconds)
                                    if elapsed_time_seconds >= VECTOR_ESTIMATION_TIME_SECONDS:
                                        distance_along_guide = np.dot(shift, guide_vector) / (np.linalg.norm(guide_vector)**2)
                                        orthogonal_vector = shift - distance_along_guide * guide_vector        
                                        guide_vector_orthogonal = orthogonal_vector / elapsed_time_seconds

                                        print('guide vector orthogonal: ', guide_vector_orthogonal)
                                        print('angle between vectors: ', angle_between_vectors(guide_vector, guide_vector_orthogonal))
                                        

                                        r.publish(messages.STATUS_GUIDE_VECTOR_DEC, redis_helpers.toRedis(guide_vector_orthogonal))

                                        current_state = AdjusterStates.GUIDING
                                        filtered_adjustment_dec = 1 #start speeding back towards origin
                                        raw_adjustment_dec = 1

                            elif current_state == AdjusterStates.START_GUIDING_DIR_ORTH_2:
                                print('dir_orth_2, orth distance = ', orthogonal_distance)

                                if orthogonal_distance < 0:
                                    print('back to origin, moving to guiding')
                                    filtered_adjustment_dec = 0
                                    raw_adjustment_dec = 0
                                    current_state = AdjusterStates.GUIDING

                                #TODO: back to original position

                            elif current_state == AdjusterStates.GUIDING:
                                
                                orthogonal_vector = shift - parallel_distance * guide_vector                        

                                #TODO: filter realllll slow instead of just making it slow
                                raw_adjustment_dec = orthogonal_distance / ORTHOGONAL_ADJUSTMENT_TARGET_SECONDS
                                filtered_adjustment_dec = np.clip(raw_adjustment_dec, -MAX_ADJUSTMENT, MAX_ADJUSTMENT)


                        r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(filtered_adjustment_ra))
                        r.publish(messages.STATUS_CURRENT_RAW_ADJUSTMENT, redis_helpers.toRedis(raw_adjustment_ra))
                        r.publish(messages.STATUS_PARALLEL_ERROR, redis_helpers.toRedis(parallel_distance))
                        r.publish(messages.STATUS_ORTHOGONAL_ERROR, redis_helpers.toRedis(orthogonal_distance))
                        r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(filtered_adjustment_dec))

                        guiding_status = {'drift_x' : str(shift[1]), 'drift_y' : str(shift[0]), 
                                        'parallel_error' : str(parallel_distance), 'orthogonal_error' : str(orthogonal_distance),
                                        'raw_adjustment_ra' : str(raw_adjustment_ra), 'filtered_adjustment_ra' : str(filtered_adjustment_ra),
                                        'raw_adjustment_dec' : str(raw_adjustment_dec), 'filtered_adjustment_dec' : str(filtered_adjustment_dec)
                                        }
                        r.publish(messages.STATUS_GUIDING_STATUS, redis_helpers.toRedis(guiding_status))


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
