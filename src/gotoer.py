import redis_helpers
import redis

from astropy.coordinates import SkyCoord

import datetime
import messages

class Gotoer(object):
        def __init__(self):	
        	self.goto_in_progress = False
        	self.goto_target_ra = None
        	self.goto_target_dec = None

        	self.current_ra = None
        	self.current_dec = None


            self.r = redis.StrictRedis(host='localhost', port=6379)
            self.p = self.r.pubsub(ignore_subscribe_messages=True)
            self.p.subscribe(**{messages.CMD_GOTO_POSITION : self.goto_position,
                                messages.STATUS_DISPLAY_CURRENT_RA_DEC: self.update_current_position,
                                messages.STOP_ALL : self.stop_all_handler})

            self.thread = self.p.run_in_thread(sleep_time = 0.1)

        def stop_all_handler(self):
            self.thread.stop()

        def goto_position(self, message):
        	self.goto_target_ra, self.goto_target_dec = redis_helpers.fromRedis(message['data'])
        	self.goto_in_progress = True

        	ra_diff = self.goto_target_ra - self.current_ra

        	ra_speed = 100

        	if ra_diff > 0:
        		self.ra_direction = 1
        		self.r.publish(messages.ra_forward_start, redis_helpers.toRedis(ra_speed))
        	else:
        		self.ra_direction = -1
        		self.r.publish(messages.ra_backward_start, redis_helpers.toRedis(ra_speed))


        def update_current_position(self, message):
        	self.current_ra, self.current_dec = redis_helpers.fromRedis(message['data'])
        	if self.goto_in_progress:
        		ra_diff = self.goto_target_ra - self.current_ra

        		if self.ra_direction * ra_diff < 0:
        			if self.ra_direction == 1:
        				self.r.publish(messages.ra_forward_stop)
        			else:
        				self.r.publish(messages.ra_backward_stop)