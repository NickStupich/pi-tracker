import redis_helpers
import redis

import datetime

import messages
from flask.json import jsonify

class UpdatesListener(object):
    def __init__(self, socketio):

        self.socketio = socketio
        self.current_values = {}

        r = redis.StrictRedis(host='localhost', port=6379) 
        self.p = r.pubsub(ignore_subscribe_messages=True)

        self.add_simple_parameter(messages.STATUS_MAX_PIXEL_VALUE, -1)
        self.add_simple_parameter(messages.STATUS_CURRENT_TRACKING_POSITION, "")
        self.add_simple_parameter(messages.STATUS_STARTING_TRACKING_POSITION, "")
        self.add_simple_parameter(messages.CMD_SET_SHUTTER_SPEED, 300)
        self.add_simple_parameter(messages.CMD_SET_VISUAL_GAIN, 10)
        self.add_simple_parameter(messages.STATUS_CURRENT_RAW_ADJUSTMENT, 1)
        self.add_simple_parameter(messages.STATUS_PARALLEL_ERROR, 0)
        self.add_simple_parameter(messages.STATUS_ORTHOGONAL_ERROR, 0)
        self.add_simple_parameter(messages.STATUS_DRIFT_X)
        self.add_simple_parameter(messages.STATUS_DRIFT_Y)
        self.add_simple_parameter(messages.STATUS_GUIDE_VECTOR_RA)
        self.add_simple_parameter(messages.STATUS_GUIDE_VECTOR_DEC)

        self.add_simple_parameter(messages.CMD_SET_SPEED_ADJUSTMENT_RA)
        self.add_simple_parameter(messages.CMD_SET_SPEED_ADJUSTMENT_DEC)

        self.add_simple_parameter(messages.STATUS_CALIBRATION_DRIFT_ARC_SECONDS)
        self.add_simple_parameter(messages.STATUS_FAILED_TRACKING_COUNT)
        
        self.add_json_parameter(messages.STATUS_GUIDING_STATUS)
        
        #self.add_simple_parameter(messages.STATUS_RA_POSITION)
        #self.add_simple_parameter(messages.STATUS_DEC_POSITION)
        #self.p.subscribe(**{messages.STATUS_RA_POSITION : self.updatePosition})
        #self.p.subscribe(**{messages.STATUS_DEC_POSITION : self.updatePosition})
        self.add_simple_parameter(messages.STATUS_DISPLAY_CURRENT_RA_DEC)

        self.p.subscribe(**{messages.STOP_ALL: self.stop_all_handler,
                            messages.STATUS_GET_ALL_STATUS : self.get_all_status})

        self.thread = self.p.run_in_thread(sleep_time = 0.1)

    def add_simple_parameter(self, key, initialValue = ''):
        # self.current_values[key] = initialValue
        self.p.subscribe(**{key : self.updateSimpleParameter})

    def add_json_parameter(self, key):
        self.p.subscribe(**{key : self.updateJsonParameter})

    def updateSimpleParameter(self, message):
        channel = message['channel'].decode('ASCII')
        raw_data = redis_helpers.fromRedis(message['data'])
        string_value = str(raw_data)
        self.socketio.emit(channel, {'value': string_value}, namespace='/test')
        self.current_values[str(channel)] = str(raw_data)

    def updateJsonParameter(self, message):
        channel = message['channel'].decode('ASCII')
        raw_data = redis_helpers.fromRedis(message['data'])
        #print(channel, raw_data)
        self.socketio.emit(channel, {'value': raw_data}, namespace='/test')
        self.current_values[str(channel)] = raw_data

    def updatePosition(self, message):
        channel = message['channel'].decode('ASCII')
        position = redis_helpers.fromRedis(message['data'])
        #position_str = "%02dh%02dm%02ds" % (position[0], position[1], position[2])
        position_str = "%d arcseconds" % position
        self.socketio.emit(channel, {'value' : position_str}, namespace='/test')
        self.current_values[str(channel)] = position_str

    def stop_all_handler(self):
        self.thread.stop()

    def get_all_status(self, message):
        print('update all')
        for channel in self.current_values:
            value = self.current_values[channel]
            self.socketio.emit(channel, {'value' : value}, namespace='/test')
