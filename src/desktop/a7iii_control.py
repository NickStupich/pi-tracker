import time
import threading
from datetime import datetime
import threading
import messages
import redis_helpers
import redis
import numpy as np
import matplotlib.pyplot as plt
import os
import imageio

import rawpy
import gphoto2 as gp
import subprocess

class A7iiiControl(threading.Thread):

    def __init__(self
                ):
        threading.Thread.__init__(self)

        self.r = redis.StrictRedis(host='localhost', port=6379) 
        self.p = self.r.pubsub(ignore_subscribe_messages=True)
        self.kill = False
        self.p.subscribe(**{messages.STOP_ALL:self.stop_all_handler,
            })

        self.thread = self.p.run_in_thread(sleep_time = 0.01)

    def stop_all_handler(self, message):
        self.kill = True


def list_camera_files(camera, path='/'):
    result = []
    # get files
    gp_list = gp.check_result(
        gp.gp_camera_folder_list_files(camera, path))
    for name, value in gp_list:
        result.append(os.path.join(path, name))
    # read folders
    folders = []
    gp_list = gp.check_result(
        gp.gp_camera_folder_list_folders(camera, path))
    for name, value in gp_list:
        folders.append(name)
    # recurse over subfolders
    for name in folders:
        result.extend(list_camera_files(camera, os.path.join(path, name)))
    return result

def test_take_gphoto(exposure_time_seconds = 2):
    camera = gp.Camera()
    camera.init()

    #file_path = camera.capture(gp.GP_CAPTURE_IMAGE)

    
    
    config = camera.get_config()
    OK, bulb_child = gp.gp_widget_get_child_by_name(config, 'bulb')
    bulb_child.set_value(1)
    camera.set_config(config)

    time.sleep(exposure_time_seconds)

    bulb_child.set_value(0)
    camera.set_config(config)

    # camera_files = list_camera_files(camera)
    # print(camera_files)

    timeout = 3000 # miliseconds
    while True:
        event_type, event_data = camera.wait_for_event(timeout)
        if event_type == gp.GP_EVENT_FILE_ADDED:
            cam_file = camera.file_get(
                event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
            target_path = os.path.join(os.getcwd(), event_data.name)
            print("Image is being saved to {}".format(target_path))
            cam_file.save(target_path)
        elif event_type == gp.GP_EVENT_TIMEOUT:
            break
        else:
            # print(event_type)
            pass


    #print(help(camera.capture))
    # print('camera file path: ', file_path.folder, file_path.name)


    #print(dir(camera))

    # target_path = 'image_capture.arw'
    # camera_file = camera.file_get(file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
    # camera_file.save(target_path)


    camera.exit()

    if 0:
        raw_img = rawpy.imread(target_path)
        img = raw_img.postprocess() #fix histogram?
        plt.imshow(img)
        plt.show()

    return target_path

def test_solve_image(image_path_raw, blind=True, arcsecperpix = (9.3,9.4), ra_est = None, dec_est = None, radius = 5, sigma=4):
    
    if 0:
        jpeg_path = '/tmp/thumb.jpeg'
        if 1:
            raw_img = rawpy.imread(image_path_raw)
            # img = raw_img.postprocess() #fix histogram?
            # plt.imshow(img)
            # plt.show()



            thumb = raw_img.extract_thumb()
            if thumb.format == rawpy.ThumbFormat.JPEG:
                # thumb.data is already in JPEG format, save as-is
                with open(jpeg_path, 'wb') as f:
                    f.write(thumb.data)
            elif thumb.format == rawpy.ThumbFormat.BITMAP:
                # thumb.data is an RGB numpy array, convert with imageio
                imageio.imsave(jpeg_path, thumb.data)
            else:
                print('no thumb?')
    else:
        jpeg_path = '/tmp/conversion.jpeg'
        raw_img = rawpy.imread(image_path_raw)
        img_rgb = raw_img.postprocess(no_auto_bright=True)

        imageio.imsave(jpeg_path, img_rgb)

    cmd = '/usr/local/astrometry/bin/solve-field {img_path} -L {arcseclow} -H {arcsechigh} -u arcsecperpix --overwrite --sigma {sigma}'.format(
                    img_path = jpeg_path, arcseclow = arcsecperpix[0], arcsechigh = arcsecperpix[1], sigma=sigma)

    if not blind:
        cmd += ' --ra {ra} --dec {dec} --radius {radius}'.format(ra=ra_est, dec=dec_est, radius=radius)

    print(cmd)
    # print('running...')
    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
    # print(output)

    ra_dec_lines = list(filter(lambda s: s.startswith('Field center: (RA,Dec)'), output.split('\n')))
    # print(ra_dec_lines)
    ra_dec_line = ra_dec_lines[0]
    # print('ra_dec line: ', ra_dec_line)
    ra_dec_portion = ra_dec_line.split('=')[-1].replace('(', '').replace(')', '').replace('deg.', '').strip()
    # print(ra_dec_portion)
    ra = float(ra_dec_portion.split(',')[0])
    dec = float(ra_dec_portion.split(',')[1])

    # print(ra, dec)

    return ra,dec

    # /usr/local/astrometry/bin/solve-field ~/DSC07653.jpg -L {ar} -H 10 -u arcsecperpix --overwrite --ra 36 --dec 64 --radius 5

def test_take_and_solve():
    img_path = test_take_gphoto(exposure_time_seconds = 5)
    start = datetime.now()
    # arcsecperpix = (9.3, 9.4)
    arcsecperpix = (2.0, 2.2)
    ra,dec = test_solve_image(img_path, arcsecperpix = arcsecperpix)
    print('solving took: ', (datetime.now() - start))
    print(ra,dec)

    if 0:
        img_path2 = test_take_gphoto()
        start = datetime.now()
        ra,dec = test_solve_image(img_path2, blind=False, ra_est = ra, dec_est = dec)
        print('solving again took: ', (datetime.now() - start))
        print(ra,dec)

    broadcast_current_position(ra, dec)

def broadcast_current_position(ra, dec):
    r = redis.StrictRedis(host='10.0.0.110', port=6379)
    r.publish(messages.CMD_SET_ABSOLUTE_CURRENT_POSITION, redis_helpers.toRedis((ra, dec)))

if __name__ == "__main__":
    test_take_and_solve()
    # test_take_gphoto()
    # test_solve_image("/home/nick/test_solving_images/DSC09619.ARW")
    # broadcast_current_position(-17, -42)