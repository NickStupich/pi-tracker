#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response, redirect, request

from wtforms import Form, StringField, TextField, validators, IntegerField, FloatField, BooleanField

# import camera driver
if os.environ.get('CAMERA'):
    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
else:
    from camera_pi import Camera
    #from camera import Camera

# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera

app = Flask(__name__)


class ShutterSpeedForm(Form):
    speed = IntegerField('Shutter Speed:', validators=[validators.required()])
    save = BooleanField('Save')
    visual_gain = IntegerField('Visual Gain:')
    overlay_tracking_history = BooleanField('Overlay tracking history')

@app.route('/')
def index():
    
    shutterSpeedForm = ShutterSpeedForm()
    shutterSpeedForm.speed.data = Camera.shutter_speed_ms
    shutterSpeedForm.save.data = Camera.save_images
    shutterSpeedForm.visual_gain.data = Camera.visual_gain
    shutterSpeedForm.overlay_tracking_history.data = Camera.overlay_tracking_history

    return render_template('index.html', camSettingsForm = shutterSpeedForm)

@app.route('/changeSettings', methods=['POST'])
def changeSettings():
    print('changeSettings()')
    newSpeed = int(request.form['speed'])
    newVisualGain = int(request.form['visual_gain'])
    save = (request.form['save'] == 'y') if 'save' in request.form else False
    overlay_tracking_history = (request.form['overlay_tracking_history'] == 'y') if 'overlay_tracking_history' in request.form else False
    Camera.update_settings(newSpeed, newVisualGain, save, overlay_tracking_history)
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
        frame = camera_func()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
