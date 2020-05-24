import time
import threading
from datetime import datetime
import threading
# from .. import messages
# import redis_helpers
import redis
import numpy as np
import matplotlib.pyplot as plt
import os
import imageio

import rawpy
import gphoto2 as gp
import subprocess


def continuous_capture_bulb(base_folder, exposure_time_seconds = 30, num_exposures = 1E3):

    output_dir = os.path.join(base_folder, datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.makedirs(output_dir)

    camera = gp.Camera()
    camera.init()

    #file_path = camera.capture(gp.GP_CAPTURE_IMAGE)



    # camera_files = list_camera_files(camera)
    # print(camera_files)
    
    config = camera.get_config()

    count = 0
    while 1:

        if count > num_exposures: break

        OK, bulb_child = gp.gp_widget_get_child_by_name(config, 'bulb')
        bulb_child.set_value(1)
        camera.set_config(config)

        time.sleep(exposure_time_seconds)

        bulb_child.set_value(0)
        camera.set_config(config)


        timeout = 3000 # miliseconds
        while True:
            event_type, event_data = camera.wait_for_event(timeout)
            if event_type == gp.GP_EVENT_FILE_ADDED:
                cam_file = camera.file_get(
                    event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
                
                #target_path = os.path.join(os.getcwd(), event_data.name)
                target_path = os.path.join(output_dir, str(count) + '.ARW')


                print("Image is being saved to {}".format(target_path))
                cam_file.save(target_path)
                break
            elif event_type == gp.GP_EVENT_TIMEOUT:
                break
            else:
                # print(event_type)
                pass

        count += 1

    camera.exit()


def continuous_capture(base_folder, exposure_time_seconds = 30, num_exposures = 1E3):

    output_dir = os.path.join(base_folder, datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.makedirs(output_dir)

    camera = gp.Camera()
    camera.init()
    
    config = camera.get_config()
    OK, speed = gp.gp_widget_get_child_by_name(config, 'shutterspeed')
    speed.set_value(str(exposure_time_seconds))
    camera.set_config(config)

    count = 0
    while 1:
        print(count)
        if count > num_exposures: break

        path = camera.capture(gp.GP_CAPTURE_IMAGE)

        event_type, event_data = camera.wait_for_event(exposure_time_seconds)
        if event_type == gp.GP_EVENT_FILE_ADDED:
            print('event file added')
        elif event_type == gp.GP_EVENT_TIMEOUT:
            print('event timeout')
        else:
            print('something else?', event_type)

        cam_file = camera.file_get(
                    path.folder, path.name, gp.GP_FILE_TYPE_NORMAL)
        
        #target_path = os.path.join(os.getcwd(), event_data.name)
        target_path = os.path.join(output_dir, str(count) + '.ARW')


        print("{} is being saved to {}".format(path.name, target_path))
        cam_file.save(target_path)


        count += 1

    camera.exit()


if __name__ == "__main__":
    continuous_capture(base_folder = '/media/sf_ubuntu', exposure_time_seconds = 30, num_exposures = 4*120)