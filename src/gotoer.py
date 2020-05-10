import redis_helpers
import redis
import numpy as np

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

        def goto_speed_calc(self, diff, max = 100, min = 2):
            result = np.abs(100 * diff)
            result = np.clip(result, min, max)
            #print(diff, result)
            return result

        def goto_position(self, message):
            self.goto_target_ra, self.goto_target_dec = redis_helpers.fromRedis(message['data'])
            self.goto_in_progress = True

            ra_diff = self.goto_target_ra - self.current_ra
            ra_speed = self.goto_speed_calc(ra_diff)

            if ra_diff < 0:
                self.ra_direction = 1
            else:
                self.ra_direction = -1
        	
            self.r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(ra_speed*self.ra_direction))


            dec_diff = self.goto_target_dec - self.current_dec
            dec_speed = self.goto_speed_calc(dec_diff)

            if dec_diff < 0:
                self.dec_direction = -1
            else:
                self.dec_direction = 1

            self.r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(dec_speed * self.dec_direction))

        def update_current_position(self, message):
            self.current_ra, self.current_dec = redis_helpers.fromRedis(message['data'])
            if self.goto_in_progress:
                ra_diff = self.goto_target_ra - self.current_ra
                if self.ra_direction * ra_diff > 0:
                    self.r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(0))
                    self.ra_direction = 0
                else:
                    new_ra_speed = self.goto_speed_calc(ra_diff)
                    self.r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(new_ra_speed * self.ra_direction))
                
                dec_diff = self.goto_target_dec - self.current_dec
                if self.dec_direction * dec_diff < 0:
                    self.r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(0))
                    self.dec_direction = 0

                if self.ra_direction == 0 and self.dec_direction == 0:
                    self.goto_in_progress = False
                    print('goto complete!')
                else:
                    new_dec_speed = self.goto_speed_calc(dec_diff)
                    self.r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(new_dec_speed * self.dec_direction))
