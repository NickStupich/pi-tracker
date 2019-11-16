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
            TrackVectorX = 7,#ca.guide_vector[0] if ca.guide_vector is not None else -1, 
            TrackVectorY = 7,#-ca.guide_vector[1] if ca.guide_vector is not None else -1,
            StartedPosition = format_number(7),#cam.tracker.starting_coords),
            CurrentPosition = format_number(7),#cam.tracker.last_coords),
            ParallelError = format_number(7),#ca.parallel_distance),
            OrthogonalError = format_number(7),#ca.orthogonal_distance),
            ErrorUpdateTime = str(7),#ca.update_time),
            ShiftX = 7,#cam.tracker.shift_x,
            ShiftY = 7,#cam.tracker.shift_y,
            ShiftUpdateTime = str(7),#cam.tracker.shift_update_time),
            CurrentAdjustment = str(7),#mc.tracking_factor),
            SmoothedAdjustment = str(7),#mc.smoothed_tracking_factor),
            AdjustmentUpdateTime = str(datetime.datetime.now()),
            NewLogs = "",
            ErrorLogs = "",
            )