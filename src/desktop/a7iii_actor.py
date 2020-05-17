import redis_helpers
import redis

import datetime
import messages
import imageio

import rawpy
import gphoto2 as gp
import subprocess
import time
import os

class a7iii_actor(object):
    def __init__(self):	
        self.r = redis.StrictRedis(host='10.0.0.111', port=6379)
        self.p = self.r.pubsub(ignore_subscribe_messages=True)
        self.p.subscribe(**{messages.CMD_SOLVE_IMAGE : self.solve_image_handler,
                            messages.STOP_ALL : self.stop_all_handler})

        self.camera = gp.Camera()
        self.camera.init()

        self.thread = self.p.run_in_thread(sleep_time = 0.1)


    def stop_all_handler(self):
        self.camera.exit()
        self.thread.stop()

    def solve_image_handler(self, msg):
        print('solve_image_handler')

        img_path = self.take_picture(exposure_time_seconds = 2)

        arcsecperpix = (9.3, 9.4)
        arcsecperpix = (2.0, 2.2)

        ra, dec = self.solve_image(img_path, arcsecperpix = arcsecperpix)

        self.r.publish(messages.CMD_SET_ABSOLUTE_CURRENT_POSITION, redis_helpers.toRedis((ra, dec)))


    def take_picture(self, exposure_time_seconds = 5):

        config = self.camera.get_config()
        OK, bulb_child = gp.gp_widget_get_child_by_name(config, 'bulb')
        bulb_child.set_value(1)
        self.camera.set_config(config)

        time.sleep(exposure_time_seconds)

        bulb_child.set_value(0)
        self.camera.set_config(config)

        # camera_files = list_camera_files(camera)
        # print(camera_files)

        timeout = 3000 # miliseconds
        while True:
            event_type, event_data = self.camera.wait_for_event(timeout)
            if event_type == gp.GP_EVENT_FILE_ADDED:
                cam_file = self.camera.file_get(
                    event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL)
                target_path = os.path.join(os.getcwd(), event_data.name)
                print("Image is being saved to {}".format(target_path))
                cam_file.save(target_path)
            elif event_type == gp.GP_EVENT_TIMEOUT:
                break
            else:
                # print(event_type)
                pass

        if 0:
            raw_img = rawpy.imread(target_path)
            img = raw_img.postprocess() #fix histogram?
            plt.imshow(img)
            plt.show()

        return target_path

    def solve_image(self, image_path_raw, blind=True, arcsecperpix = (9.3,9.4), ra_est = None, dec_est = None, radius = 5, sigma=4):
        
        jpeg_path = '/tmp/conversion.jpeg'
        raw_img = rawpy.imread(image_path_raw)
        img_rgb = raw_img.postprocess(no_auto_bright=True)

        imageio.imsave(jpeg_path, img_rgb)

        cmd = '/usr/local/astrometry/bin/solve-field {img_path} -L {arcseclow} -H {arcsechigh} -u arcsecperpix --overwrite --sigma {sigma} --cpulimit 60'.format(
                        img_path = jpeg_path, arcseclow = arcsecperpix[0], arcsechigh = arcsecperpix[1], sigma=sigma)

        if not blind:
            cmd += ' --ra {ra} --dec {dec} --radius {radius}'.format(ra=ra_est, dec=dec_est, radius=radius)

        print(cmd)
        output = subprocess.check_output(cmd, shell=True).decode('utf-8')

        ra_dec_lines = list(filter(lambda s: s.startswith('Field center: (RA,Dec)'), output.split('\n')))

        if len(ra_dec_lines) == 0:
            print('failed to solve')
            return (None, None)

        ra_dec_line = ra_dec_lines[0]
        ra_dec_portion = ra_dec_line.split('=')[-1].replace('(', '').replace(')', '').replace('deg.', '').strip()
        ra = float(ra_dec_portion.split(',')[0])
        dec = float(ra_dec_portion.split(',')[1])

        return ra,dec


if __name__ == "__main__":
    a7iii_actor()
    while 1: pass