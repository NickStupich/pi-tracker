import redis_helpers
import redis

import datetime

import messages
from flask.json import jsonify

class UpdatesListener(object):
    def __init__(self):
        self.current_values = {}

        r = redis.StrictRedis(host='localhost', port=6379) 
        self.p = r.pubsub(ignore_subscribe_messages=True)

        self.add_parameter(messages.STATUS_MAX_PIXEL_VALUE, -1)
        self.add_parameter(messages.STATUS_CURRENT_TRACKING_POSITION, "")
        self.add_parameter(messages.STATUS_STARTING_TRACKING_POSITION, "")
        self.add_parameter(messages.CMD_SET_SHUTTER_SPEED, 100)
        self.add_parameter(messages.CMD_SET_VISUAL_GAIN, 10)
        self.add_parameter(messages.STATUS_CURRENT_RAW_ADJUSTMENT, 1)
        self.add_parameter(messages.STATUS_PARALLEL_ERROR, 0)
        self.add_parameter(messages.STATUS_ORTHOGONAL_ERROR, 0)
        self.add_parameter(messages.STATUS_DRIFT_X)
        self.add_parameter(messages.STATUS_DRIFT_Y)
        self.add_parameter(messages.STATUS_GUIDE_VECTOR_X)
        self.add_parameter(messages.STATUS_GUIDE_VECTOR_Y)
        self.add_parameter(messages.CMD_SET_ADJUSTMENT_FACTOR)
        
        self.p.subscribe(**{messages.STOP_ALL: self.stop_all_handler})
        self.thread = self.p.run_in_thread(sleep_time = 0.1)

    def add_parameter(self, key, initialValue = ''):
        self.current_values[key] = initialValue
        self.p.subscribe(**{key : self.updateParameter})

    def updateParameter(self, message):
        channel = message['channel'].decode('ASCII')
        # print(channel)
        raw_data = redis_helpers.fromRedis(message['data'])
        # print('update parameter: %s, value: %s' % (channel, raw_data))

        #TODO: format better?
        self.current_values[str(channel)] = str(raw_data)

    def getParameter(self, key):
        return self.current_values[key]

    def stop_all_handler(self):
        self.thread.stop()

    def current_values_json(self):

        def format_number(x):
            if isinstance(x, tuple):
                return '\t'.join(map(format_number, x))
            elif x is None:
                return 'None'
            else:
                return '%.1f' % x

        return jsonify(
            FailedTrackCount = 7,#cam.failed_track_count,
            MeanAdjustment = str(7),#mc.tracking_factor),
            MaxPixelValue = self.current_values[messages.STATUS_MAX_PIXEL_VALUE],
            TrackVectorX = str(self.current_values[messages.STATUS_GUIDE_VECTOR_X]),
            TrackVectorY = str(self.current_values[messages.STATUS_GUIDE_VECTOR_Y]),
            StartedPosition = str(self.current_values[messages.STATUS_STARTING_TRACKING_POSITION]),
            CurrentPosition = str(self.current_values[messages.STATUS_CURRENT_TRACKING_POSITION]),
            ParallelError = str(self.current_values[messages.STATUS_PARALLEL_ERROR]),
            OrthogonalError = str(self.current_values[messages.STATUS_ORTHOGONAL_ERROR]),
            ErrorUpdateTime = str(datetime.datetime.now()),
            ShiftX = str(self.current_values[messages.STATUS_DRIFT_X]),
            ShiftY = str(self.current_values[messages.STATUS_DRIFT_Y]),
            ShiftUpdateTime = str(datetime.datetime.now()),
            CurrentAdjustment = str(self.current_values[messages.STATUS_CURRENT_RAW_ADJUSTMENT]),
            SmoothedAdjustment = str(self.current_values[messages.CMD_SET_ADJUSTMENT_FACTOR]),
            AdjustmentUpdateTime = str(datetime.datetime.now()),
            NewLogs = "",
            ErrorLogs = "",
            )