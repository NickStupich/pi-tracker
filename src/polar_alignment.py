import sys
import os

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

import redis_helpers
import redis

import datetime
import messages
import imageio

import rawpy
import gphoto2 as gp
import subprocess
import time
from astropy.time import Time
from astropy.coordinates import EarthLocation, SkyCoord

from two_star_align import get_polar_align_error


vancouver_location = EarthLocation(lat=49.3124536, lon = -123.0756053)
HOME_LATITUDE = 49.3124536

class PoleFindingStates:
    IDLE = 0
    SOLVE_1 = IDLE + 1
    GOTO = SOLVE_1 + 1
    SOLVE_2 = GOTO + 1

def get_sidereel_degrees():
    t = Time(datetime.datetime.utcnow(), scale='utc', location=vancouver_location)
    t.delta_ut1_utc = 0
    sidereel_degrees = t.sidereal_time('mean').degree
    return sidereel_degrees

class polar_alignment_actor(object):
    def __init__(self): 
        self.r = redis.StrictRedis(host='10.0.0.111', port=6379)
        self.p = self.r.pubsub(ignore_subscribe_messages=True)
        self.p.subscribe(**{messages.CMD_CALCULATE_POLAR_ALIGNMENT_ERROR : self.start_polar_alignment_calculation_handler,
                            messages.STOP_ALL : self.stop_all_handler,
                            messages.CMD_SET_IMAGE_SOLVING_ERROR : self.set_image_solving_error,
                            messages.STATUS_GOTO_COMPLETE : self.goto_complete_handler,
                            })

        self.state = PoleFindingStates.IDLE
        self.thread = self.p.run_in_thread(sleep_time = 0.1)


    def start_polar_alignment_calculation_handler(self, msg):
        print('start polar alignment')
        self.state = PoleFindingStates.SOLVE_1
        self.r.publish(messages.CMD_SOLVE_IMAGE, redis_helpers.toRedis(""))
        print('starting solve1')

    def set_image_solving_error(self, message):
        print('absolute current position handler')
        ra, dec, ra_error, dec_error = redis_helpers.fromRedis(message['data'])
        if self.state == PoleFindingStates.SOLVE_1:
            print('got solve1 result')
            sidereel_degrees = get_sidereel_degrees()
            self.ha1 = sidereel_degrees - ra
            self.dec1 = dec

            self.state = GOTO
            new_ra_target = ra + 90
            new_dec_target = dec

            self.r.publish(messages.CMD_GOTO_POSITION, redis_helpers.toRedis((new_ra_target, new_dec_target)))

        elif self.state == PoleFindingStates.SOLVE_2:
            print('got solve2 result')
            sidereel_degrees = get_sidereel_degrees()
            self.ha2 = sidereel_degrees - ra
            self.dec2 = dec
            self.err_ra = ra_error
            self.err_dec = dec_error

            self.calc_broadcast_alignment_error()


    def calc_broadcast_alignment_error(self):
        print('calculating polar alignment error')
        err_elevation, err_azimuth = get_polar_align_error(self.ha1, self.dec1, self.ha2, self.dec2, self.err_ra, self.err_dec, HOME_LATITUDE)

        print('elevation error: ', err_elevation)
        print('err_azimuth: ', err_azimith)

        self.r.publish(messages.STATUS_POLAR_ALIGNMENT_RESULT, redis_helpers.toRedis(""))

    def goto_complete_handler(self, msg):
        print('goto complete handler')
        
        if self.state == GOTO:
            print('starting solve2')
            self.state = SOLVE_2
            self.r.publish(messages.CMD_SOLVE_IMAGE, redis_helpers.toRedis(""))

    def stop_all_handler(self):
        self.thread.stop()


if __name__ == "__main__":
    paa = polar_alignment_actor()

    while 1:
        time.sleep(1)

