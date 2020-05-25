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

class polar_alignment_actor(object):
    def __init__(self): 
        self.r = redis.StrictRedis(host='10.0.0.111', port=6379)
        self.p = self.r.pubsub(ignore_subscribe_messages=True)
        self.p.subscribe(**{messages.CMD_CALCULATE_POLAR_ALIGNMENT_ERROR : self.start_polar_alignment_calculation_handler,
                            messages.STOP_ALL : self.stop_all_handler,
                            messages.CMD_SET_IMAGE_SOLVING_ERROR : self.set_image_solving_error,
                            messages.STATUS_GOTO_COMPLETE : self.goto_complete_handler,
                            })


    def start_polar_alignment_calculation_handler(self, msg):
        print('start polar alignment')

    def set_image_solving_error(self, msg):
        print('absolute current position handler')

    def goto_complete_handler(self, msg):
        print('goto complete handler')

    def stop_all_handler(self):
        self.thread.stop()


if __name__ == "__main__":
    paa = polar_alignment_actor()

    while 1:
        time.sleep(1)

