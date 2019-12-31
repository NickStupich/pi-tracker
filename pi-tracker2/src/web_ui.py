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


log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from wtforms import Form, StringField, TextField, validators, IntegerField, FloatField, BooleanField

new_logs = ""
error_logs = ""
import sys

def log_new_write(message):
    global new_logs
    new_logs += message  

def err_new_write(message):
    global error_logs
    error_logs += message

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

app = Flask(__name__)
# async_mode = "eventlet"
# async_mode = "gevent"
async_mode = "threading"
socketio = SocketIO(app, async_mode=async_mode, ping_timeout=30, logger=False, engineio_logger=False)

r = redis.StrictRedis(host='localhost', port=6379) 

import updates_listener
updates = updates_listener.UpdatesListener(socketio)

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@socketio.on('set_shutter_speed', namespace='/test')
def setShutterSpeed(value):
    r.publish(messages.CMD_SET_SHUTTER_SPEED, redis_helpers.toRedis(int(value)))

@socketio.on('set_visual_gain', namespace='/test')
def setVisualGain(value):
    r.publish(messages.CMD_SET_VISUAL_GAIN, redis_helpers.toRedis(int(value)))

@socketio.on('startTracking', namespace='/test')
def startRestartTracking():
    r.publish(messages.CMD_START_TRACKING, "")
    return redirect('/')

@socketio.on('stopTracking', namespace='/test')
def stopTracking():
    r.publish(messages.CMD_STOP_TRACKING, "")
    return redirect('/')

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
    return redirect('/')

@socketio.on('enable_movement', namespace='/test')
def enable_movement():    
    r.publish(messages.CMD_ENABLE_MOVEMENT, "")
    return redirect('/')

@socketio.on('start_guiding', namespace='/test')
def start_guiding():
    r.publish(messages.CMD_START_GUIDING, "")
    return redirect('/')

@socketio.on('stop_guiding', namespace='/test')
def stop_guiding():
    r.publish(messages.CMD_STOP_GUIDING, "")
    return redirect('/')

@socketio.on('dec_back_start', namespace='/test')
def dec_back_start(speed):
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(-speed))
    print('dec_back_start()', speed)
    return ""
@socketio.on('dec_back_stop', namespace='/test')
def dec_back_stop():
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(0))
    print('dec_back_stop()')
    return ""
@socketio.on('dec_forward_start', namespace='/test')
def dec_forward_start(speed):
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(speed))
    print('dec_forward_start()', speed)
    return ""
@socketio.on('dec_forward_stop', namespace='/test')
def dec_forward_stop():
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_DEC, redis_helpers.toRedis(0))
    print('dec_forward_stop()')
    return ""

@socketio.on('ra_back_start', namespace='/test')
def ra_back_start(speed):
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(-speed))
    print('ra_back_start()', speed)
    return ""
@socketio.on('ra_back_stop', namespace='/test')
def ra_back_stop():
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(0))
    print('ra_back_stop()')
    return ""
@socketio.on('ra_forward_start', namespace='/test')
def ra_forward_start(speed):
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(speed))
    print('ra_forward_start()', speed)
    return ""
@socketio.on('ra_forward_stop', namespace='/test')
def ra_forward_stop():
    r.publish(messages.CMD_SET_SPEED_ADJUSTMENT_RA, redis_helpers.toRedis(0))
    print('ra_forward_stop()')
    return ""

def run():
    socketio.run(app, debug=False)

if __name__ == "__main__":
    run()
