import redis_helpers
import redis

import datetime
import messages

from astropy.time import Time
from astropy.coordinates import EarthLocation, SkyCoord

vancouver_location = EarthLocation(lat=49.3, lon = -123.1)

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
                self.relative_dec_degrees = 0
                self.relative_ra_degrees = 0

                self.ra_zero_pos_degrees = 0
                self.dec_zero_pos_degrees = 0

        def stop_all_handler(self):
                self.thread.stop()

        def set_absolute_position_handler(self, message):
                ra, dec = redis_helpers.fromRedis(message['data'])
                print('received absolute position update: ', ra, dec)

                if ra is None or dec is None:
                    print('getting absolute position failed, ignoring None(s)')
                else:
                    new_ra_zero_pos = self.relative_ra_degrees - ra
                    new_dec_zero_pos = self.relative_dec_degrees - dec

                    print('coodinate zero pos update deltas: ', self.ra_zero_pos_degrees - new_ra_zero_pos, self.dec_zero_pos_degrees - new_dec_zero_pos)

                    self.ra_zero_pos_degrees = new_ra_zero_pos
                    self.dec_zero_pos_degrees = new_dec_zero_pos


                    #self.ra_zero_pos_degrees = self.relative_ra_degrees - ra
                    #self.dec_zero_pos_degrees = self.relative_dec_degrees - dec

        def update_dec_handler(self, message):
                self.relative_dec_degrees += redis_helpers.fromRedis(message['data'])
                self.on_new_position()

        def update_ha_handler(self, message):
                self.ha_relative_degrees += redis_helpers.fromRedis(message['data'])
                self.on_new_position()

        def on_new_position(self):
                t = Time(datetime.datetime.utcnow(), scale='utc', location=vancouver_location)
                t.delta_ut1_utc = 0
                sidereal_degrees = t.sidereal_time('mean').degree
                self.relative_ra_degrees = sidereal_degrees - self.ha_relative_degrees               

                absolute_ra_degrees = self.relative_ra_degrees - self.ra_zero_pos_degrees
                absolute_dec_degrees = self.relative_dec_degrees - self.dec_zero_pos_degrees
                c = SkyCoord(ra=absolute_ra_degrees, dec=absolute_dec_degrees, frame='icrs', unit='deg')
                ra_output = '%dh%02dm%.2fs' % (c.ra.hms)
                dec_output = '%dd%2d%.1fs' % (c.dec.dms)

                #output_str = '%s/%s' % (ra_output, dec_output)

                #c = SkyCoord(ra=absolute_ra_degrees, dec=absolute_dec_degrees, frame='icrs', unit='deg')
                #ra_output = '%dh%02dm%.2fs' % (c.ra.hms)
                #dec_output = '%dd%2d%.1fs' % (c.dec.dms)

                #output_str = '%s/%s' % (ra_output, dec_output)
                #self.r.publish(messages.STATUS_DISPLAY_CURRENT_RA_DEC, redis_helpers.toRedis(output_str))                
                self.r.publish(messages.STATUS_DISPLAY_CURRENT_RA_DEC, redis_helpers.toRedis((absolute_ra_degrees, absolute_dec_degrees)))
