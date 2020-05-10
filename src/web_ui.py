#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response, redirect, request
from flask_socketio import SocketIO, emit
import numpy as np
import cv2
import logging
from datetime import datetime
import messages
import time
import redis_helpers
import redis
import functools

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from wtforms import Form, StringField, TextField, validators, IntegerField, FloatField, BooleanField

app = Flask(__name__)
# async_mode = "eventlet"
# async_mode = "gevent"
async_mode = "threading"
socketio = SocketIO(app, async_mode=async_mode, ping_timeout=30, logger=False, engineio_logger=False)

import sys
def log_new_write(message):
    socketio.emit("log_msg", {'value': message}, namespace='/test')

def err_new_write(message):
    socketio.emit("error_msg", {'value': message}, namespace='/test')

class Logger(object):
    def __init__(self, original_stream, new_write):
        self.terminal = original_stream
        self.new_write = new_write

    def write(self, message):
        self.terminal.write(message)
        self.new_write(message)

    def flush(self):
        self.terminal.flush()

sys.stdout = Logger(sys.stdout, log_new_write)
sys.stderr = Logger(sys.stderr, err_new_write)

r = redis.StrictRedis(host='localhost', port=6379) 

import updates_listener
updates = updates_listener.UpdatesListener(socketio)

def get_current_status():
    p = r.pubsub(ignore_subscribe_messages=True)   

    status = {messages.STATUS_TRACKING_STATUS : None,
        messages.STATUS_MOVEMENT_STATUS : None,
        messages.STATUS_GUIDING_STATUS : None,
        messages.STATUS_DITHERING_STATUS : None
        }

    for key in status.keys():
        p.subscribe(key)

    r.publish(messages.STATUS_GET_ALL_STATUS, "")

    while 1:
        message = p.get_message()
        if message:
            channel = message['channel'].decode('ASCII')
            data = redis_helpers.fromRedis(message['data'])
            if channel in status:
                status[channel] = data

                finished = functools.reduce(lambda a, b: a and b, map(lambda x: x is not None, status.values()))
                if finished: 
                    break
        time.sleep(0.1)

    return status

@app.route('/')
def index():

    status = get_current_status()

    def to_bool(x):
        return  'checked="true"' if x else ""

    result = render_template('index.html', async_mode=socketio.async_mode,
        is_tracking = to_bool(status[messages.STATUS_TRACKING_STATUS]), 
        is_moving = to_bool(status[messages.STATUS_MOVEMENT_STATUS]), 
        is_guiding=to_bool(status[messages.STATUS_GUIDING_STATUS]), 
        is_dithering = to_bool(status[messages.STATUS_DITHERING_STATUS]),
        )
    
    return result

@socketio.on('set_shutter_speed', namespace='/test')
def setShutterSpeed(value):
    r.publish(messages.CMD_SET_SHUTTER_SPEED, redis_helpers.toRedis(int(value)))

@socketio.on('set_visual_gain', namespace='/test')
def setVisualGain(value):
    r.publish(messages.CMD_SET_VISUAL_GAIN, redis_helpers.toRedis(int(value)))

@socketio.on('goto_position', namespace='/test')
def goto_position(ra_h, ra_m, ra_s, dec_d, dec_m, dec_s):
    def pos_to_num(pos_str):
        if len(pos_str.strip()) > 0:
            return float(pos_str)
        else:
            return 0
    print('goto_position', ra_h, ra_m, ra_s, dec_d, dec_m, dec_s)
    r.publish(messages.CMD_GOTO_POSITION, redis_helpers.toRedis((pos_to_num(ra_h), pos_to_num(ra_m), pos_to_num(ra_s), pos_to_num(dec_d), pos_to_num(dec_m), pos_to_num(dec_s))))

@socketio.on('startTracking', namespace='/test')
def startRestartTracking():
    r.publish(messages.CMD_START_TRACKING, "")

@socketio.on('stopTracking', namespace='/test')
def stopTracking():
    r.publish(messages.CMD_STOP_TRACKING, "")

def gen_frame(msg_type):
    r2 = redis.StrictRedis(host='localhost', port=6379) 
    p = r2.pubsub(ignore_subscribe_messages=True)
    p.subscribe(msg_type)

    for message in p.listen():
        data = message['data']
        jpeg_bytes = redis_helpers.fromRedis(data)

        newImageContent = (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')

        yield newImageContent

@app.route('/video_feed')
def video_feed():
    return Response(gen_frame(messages.NEW_PREVIEW_FRAME), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/subimg_video_feed')
def subimg_video_feed():
    return Response(gen_frame(messages.NEW_SUB_PREVIEW_FRAME), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('disable_movement', namespace='/test')
def disable_movement():
    r.publish(messages.CMD_DISABLE_MOVEMENT, "")

@socketio.on('enable_movement', namespace='/test')
def enable_movement():    
    r.publish(messages.CMD_ENABLE_MOVEMENT, "")

@socketio.on('start_guiding', namespace='/test')
def start_guiding():
    r.publish(messages.CMD_START_GUIDING, "")

@socketio.on('stop_guiding', namespace='/test')
def stop_guiding():
    r.publish(messages.CMD_STOP_GUIDING, "")

@socketio.on('enable_dithering', namespace='/test')
def enable_dithering():
    r.publish(messages.CMD_START_DITHERING, "")

@socketio.on('disable_dithering', namespace='/test')
def disable_dithering():
    r.publish(messages.CMD_STOP_DITHERING, "")

@socketio.on('set_dithering_magnitude', namespace='/test')
def set_dithering_magnitude(magnitude):
    r.publish(messages.CMD_SET_DITHERING_MAGNITUDE, redis_helpers.toRedis(magnitude))

@socketio.on('set_dithering_interval', namespace='/test')
def set_dithering_interval(seconds):
    r.publish(messages.CMD_SET_DITHERING_INTERVAL, redis_helpers.toRedis(seconds))
@socketio.on('dec_back_start', namespace='/test')
def dec_back_start(speed):
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(-speed))
@socketio.on('dec_back_stop', namespace='/test')
def dec_back_stop():
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(0))
@socketio.on('dec_forward_start', namespace='/test')
def dec_forward_start(speed):
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(speed))
@socketio.on('dec_forward_stop', namespace='/test')
def dec_forward_stop():
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(0))

@socketio.on('ra_back_start', namespace='/test')
def ra_back_start(speed):
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(-speed))
@socketio.on('ra_back_stop', namespace='/test')
def ra_back_stop():
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(0))
@socketio.on('ra_forward_start', namespace='/test')
def ra_forward_start(speed):
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(speed))
@socketio.on('ra_forward_stop', namespace='/test')
def ra_forward_stop():
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(0))

def run():
    socketio.run(app, debug=False, host='0.0.0.0')

if __name__ == "__main__":
    run()
