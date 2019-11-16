#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response, redirect, request
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

import updates_listener
updates = updates_listener.UpdatesListener()

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
r = redis.StrictRedis(host='localhost', port=6379) 

class ShutterSpeedForm(Form):
    speed = IntegerField('Shutter Speed:', validators=[validators.required()])
    save = BooleanField('Save')
    visual_gain = IntegerField('Visual Gain:')
    overlay_tracking_history = BooleanField('Overlay tracking history')
    subPixelFit = BooleanField('Sub Pixel Fit')
    ema_factor = FloatField('Ema factor:')

@app.route('/')
def index():
    
    shutterSpeedForm = ShutterSpeedForm()
    shutterSpeedForm.speed.data = 7#cam.shutter_speed_ms
    shutterSpeedForm.save.data = 0#Camera.save_images
    shutterSpeedForm.visual_gain.data = 0#Camera.visual_gain
    shutterSpeedForm.overlay_tracking_history.data = 0#Camera.overlay_tracking_history
    shutterSpeedForm.subPixelFit.data = 0#Camera.subPixelFit
    shutterSpeedForm.ema_factor.data = 0# MotorControl.ema_factor

    return render_template('index.html', camSettingsForm = shutterSpeedForm)

@app.route('/changeSettings', methods=['POST'])
def changeSettings():
    print('changeSettings()')
    newSpeed = int(request.form['speed'])
    newVisualGain = int(request.form['visual_gain'])
    save = (request.form['save'] == 'y') if 'save' in request.form else False
    overlay_tracking_history = (request.form['overlay_tracking_history'] == 'y') if 'overlay_tracking_history' in request.form else False
    subPixelFit = (request.form['subPixelFit'] == 'y') if 'subPixelFit' in request.form else False
    ema_factor = float(request.form['ema_factor'])
    #Camera.update_settings(newSpeed, newVisualGain, save, overlay_tracking_history, subPixelFit)
    
    #TODO
    # pub.sendMessage(messages.SET_SHUTTER_SPEED, new_speed_ms = newSpeed)
    
    #MotorControl().set_ema_factor(ema_factor)
    return redirect('/')

@app.route('/startRestartTracking', methods=['POST'])
def startRestartTracking():
    r.publish(messages.CMD_START_TRACKING, "")
    return redirect('/')


@app.route('/stopTracking', methods=['POST'])
def stopTracking():
    r.publish(messages.CMD_STOP_TRACKING, "")
    return redirect('/')

def gen_frame(msg_type):

    # print('gen_frame: ', msg_type)
    r2 = redis.StrictRedis(host='localhost', port=6379) 
    p = r2.pubsub(ignore_subscribe_messages=True)
    p.subscribe(msg_type)

    for message in p.listen():
        data = message['data']
        img = redis_helpers.fromRedis(data)

        ret, jpeg = cv2.imencode('.jpg', img)
        newImageContent = (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

        yield newImageContent

@app.route('/video_feed')
def video_feed():
    return Response(gen_frame(messages.NEW_IMAGE_FRAME), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/subimg_video_feed')
def subimg_video_feed():
    return Response(gen_frame(messages.NEW_SUB_IMAGE_FRAME), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/disable_movement', methods=['POST'])
def disable_movement():
    r.publish(messages.CMD_DISABLE_MOVEMENT, "")
    return redirect('/')
    

@app.route('/enable_movement', methods=['POST'])
def enable_movement():    
    r.publish(messages.CMD_ENABLE_MOVEMENT, "")
    return redirect('/')
    
@app.route('/start_following', methods=['POST'])
def start_following():

    # ca = CameraAdjuster()
    # ca.start_guiding()
    return redirect('/')

@app.route('/updates', methods= ['GET'])
def update_status():
    global new_logs, error_logs
    global max_pixel_value
    logs_copy = new_logs
    errors_copy = error_logs
    error_logs = ""
    new_logs = ""

    return updates.current_values_json()


@app.route('/stop_following', methods=['POST'])
def stop_following():
    # ca = CameraAdjuster()
    # ca.stop_guiding()
    return redirect('/')

def run():
    app.run(host='0.0.0.0', threaded=True)
