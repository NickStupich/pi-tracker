#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response, redirect, request
from flask.json import jsonify
import numpy as np
import cv2

from wtforms import Form, StringField, TextField, validators, IntegerField, FloatField, BooleanField


import is_pi

# import camera driver
if os.environ.get('CAMERA'):
    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
else:
    if is_pi.is_pi:
        from camera_pi import Camera
    else:
        from camera import Camera
    
from motor_control import MotorControl
from camera_adjuster import CameraAdjuster

# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera

app = Flask(__name__)


class ShutterSpeedForm(Form):
    speed = IntegerField('Shutter Speed:', validators=[validators.required()])
    save = BooleanField('Save')
    visual_gain = IntegerField('Visual Gain:')
    overlay_tracking_history = BooleanField('Overlay tracking history')
    subPixelFit = BooleanField('Sub Pixel Fit')

@app.route('/')
def index():
    
    shutterSpeedForm = ShutterSpeedForm()
    shutterSpeedForm.speed.data = Camera.shutter_speed_ms
    shutterSpeedForm.save.data = Camera.save_images
    shutterSpeedForm.visual_gain.data = Camera.visual_gain
    shutterSpeedForm.overlay_tracking_history.data = Camera.overlay_tracking_history
    shutterSpeedForm.subPixelFit.data = Camera.subPixelFit

    return render_template('index.html', camSettingsForm = shutterSpeedForm)

@app.route('/changeSettings', methods=['POST'])
def changeSettings():
    print('changeSettings()')
    newSpeed = int(request.form['speed'])
    newVisualGain = int(request.form['visual_gain'])
    save = (request.form['save'] == 'y') if 'save' in request.form else False
    overlay_tracking_history = (request.form['overlay_tracking_history'] == 'y') if 'overlay_tracking_history' in request.form else False
    subPixelFit = (request.form['subPixelFit'] == 'y') if 'subPixelFit' in request.form else False
    Camera.update_settings(newSpeed, newVisualGain, save, overlay_tracking_history, subPixelFit)
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


def gen(camera_func):
    """Video streaming generator function."""
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
    # cam = Camera()
    # if cam.tracking_enabled:
    #     print('starting tracking')
    #     cam.start_tracking()

    ca = CameraAdjuster()
    ca.start_guiding()
    return redirect('/')

@app.route('/updates', methods= ['GET'])
def stuff():

    cam = Camera()
    ca = CameraAdjuster()
    mc = MotorControl()
    
    return jsonify(
        FailedTrackCount = 0,
        MeanDelay = np.mean(mc.all_delays) if len(mc.all_delays) > 0 else -1,
        MaxPixelValue = int(np.max(cam.raw_frame)),
        OrthogonalError = CameraAdjuster.orthogonal_distance,
        TrackVectorX = ca.guide_vector[0] if ca.guide_vector is not None else -1, 
        TrackVectorY = -ca.guide_vector[1] if ca.guide_vector is not None else -1,
        )


@app.route('/stop_following', methods=['POST'])
def stop_following():
    ca = CameraAdjuster()
    ca.stop_guiding()
    return redirect('/')

if __name__ == '__main__':
    cam = Camera()
    ca = CameraAdjuster(cam)
    mc = MotorControl()
    app.run(host='0.0.0.0', threaded=True)
