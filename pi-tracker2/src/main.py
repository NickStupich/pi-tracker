#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response, redirect, request
from flask.json import jsonify
import numpy as np
import cv2
import logging
from datetime import datetime
from pubsub import pub
import messages
import time

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


# import camera_pi as camera
import camera_files as camera


    
cam = camera.Camera()
cam.start()

app = Flask(__name__)


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
    shutterSpeedForm.speed.data = cam.shutter_speed_ms
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
    pub.sendMessage(messages.SET_SHUTTER_SPEED, new_speed_ms = newSpeed)
    #MotorControl().set_ema_factor(ema_factor)
    return redirect('/')

@app.route('/startRestartTracking', methods=['POST'])
def startRestartTracking():
    cam = Camera()
    cam.start_tracking() 
    return redirect('/')


@app.route('/stopTracking', methods=['POST'])
def stopTracking():
    cam = Camera()
    cam.stop_tracking() 
    return redirect('/')


hasNewImage = False
newImageContent = None
max_pixel_value = 0
@app.route('/video_feed')
def video_feed():
    def gen():
        global hasNewImage, newImageContent
        hasNewImage = False
        def new_frame_listener(frame):
            global hasNewImage, newImageContent, max_pixel_value
            max_pixel_value = np.max(frame)
            if not hasNewImage:
                ret, jpeg = cv2.imencode('.jpg', frame)
                
                newImageContent = (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                       
                hasNewImage = True
            
        pub.subscribe(new_frame_listener, messages.NEW_IMAGE_FRAME)
        
        while 1:
            if hasNewImage:
                hasNewImage = False
                yield newImageContent
            else:
                time.sleep(0.1)
    
    return Response(gen(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

hasNewSubImage = False
newSubImageContent = None
@app.route('/subimg_video_feed')
def subimg_video_feed():
    def gen():
        global hasNewSubImage, newSubImageContent
        hasNewSubImage = False
        def new_subimg_listener(frame):
            global hasNewSubImage, newSubImageContent
            if not hasNewSubImage:
                ret, jpeg = cv2.imencode('.jpg', frame)
                
                newSubImageContent = (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                       
                hasNewSubImage = True
            
        pub.subscribe(new_subimg_listener, messages.NEW_SUB_IMAGE_FRAME)
        
        while 1:
            if hasNewSubImage:
                hasNewSubImage = False
                yield newSubImageContent
            else:
                time.sleep(0.1)
    
    return Response(gen(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

"""
def gen(camera_func):
    #Video streaming generator function.
    while True:
        raw_frame, shift = camera_func()

        ret, jpeg = cv2.imencode('.jpg', raw_frame)

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')


@app.route('/video_feed')
def video_feed():
    
    cam = Camera()
    return Response(gen(cam.get_frame),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/subimg_video_feed')
def subimg_video_feed():
    
    cam = Camera()

    return Response(gen(cam.get_subimg_frame),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
"""
@app.route('/disable_movement', methods=['POST'])
def disable_movement():
    mc = MotorControl()
    mc.disable_movement()
    return redirect('/')
    

@app.route('/enable_movement', methods=['POST'])
def enable_movement():
    mc = MotorControl()
    mc.enable_movement()
    return redirect('/')
    
@app.route('/start_following', methods=['POST'])
def start_following():

    ca = CameraAdjuster()
    ca.start_guiding()
    return redirect('/')

@app.route('/updates', methods= ['GET'])
def stuff():
    print('/updates')
    #cam = Camera()
    #ca = CameraAdjuster()
    #mc = MotorControl()

    def format_number(x):
        if isinstance(x, tuple):
            return '\t'.join(map(format_number, x))
        elif x is None:
            return 'None'
        else:
            return '%.1f' % x

    global new_logs, error_logs
    global max_pixel_value
    logs_copy = new_logs
    errors_copy = error_logs
    error_logs = ""
    new_logs = ""
    return jsonify(
        FailedTrackCount = 7,#cam.failed_track_count,
        MeanAdjustment = str(7),#mc.tracking_factor),
        MaxPixelValue = str(max_pixel_value),
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
        AdjustmentUpdateTime = str(datetime.now()),
        NewLogs = logs_copy,
        ErrorLogs = errors_copy,
        )


@app.route('/stop_following', methods=['POST'])
def stop_following():
    ca = CameraAdjuster()
    ca.stop_guiding()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
