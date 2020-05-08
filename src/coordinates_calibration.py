import redis_helpers
import redis

import datetime
import messages

class CoordinatesCalibration(object):
        def __init__(self):
                self.r = redis.StrictRedis(host='localhost', port=6379)
                self.p = self.r.pubsub(ignore_subscribe_messages=True)
                self.p.subscribe(**{messages.STATUS_DEC_RELATIVE_POSITION : self.update_dec_handler,
                                    messages.STATUS_HA_RELATIVE_POSITION: self.update_ha_handler,
                                    messages.CMD_SET_ABSOLUTE_CURRENT_POSITION : self.set_absolute_position_handler,
                                    messages.STOP_ALL : self.stop_all_handler})

                self.thread = self.p.run_in_thread(sleep_time = 0.1)

                self.ha_relative_degrees = 0
                self.dec_degrees = 0

        def stop_all_handler(self):
                self.thread.stop()

        def set_absolute_position_handler(self, message):
                ra, dec = redis_helpers.fromRedis(message['data'])
                print('received absolute position update: ', ra, dec)

        def update_dec_handler(self, message):
                self.dec_degrees += redis_helpers.fromRedis(message['data'])
                self.on_new_position()

        def update_ha_handler(self, message):
                self.ha_relative_degrees += redis_helpers.fromRedis(message['data'])
                self.on_new_position()

        def on_new_position(self):
                #TODO: make this right

                

                ra_output = '%.5f' % self.ha_relative_degrees
                dec_output = '%.5f' % self.dec_degrees
                output_str = '%s/%s' % (ra_output, dec_output)
                self.r.publish(messages.STATUS_DISPLAY_CURRENT_RA_DEC, redis_helpers.toRedis(output_str))                
