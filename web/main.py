#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response, redirect, request

from wtforms import Form, StringField, TextField, validators, IntegerField, FloatField, BooleanField

# import camera driver
if os.environ.get('CAMERA'):
    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
else:
    # from camera_pi import Camera
    from camera import Camera

# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera

app = Flask(__name__)


class ShutterSpeedForm(Form):
    speed = IntegerField('Shutter Speed:', validators=[validators.required()])
    save = BooleanField('Save')

@app.route('/')
def index():
    
    shutterSpeedForm = ShutterSpeedForm()
    shutterSpeedForm.speed.data = Camera.shutter_speed_ms
    shutterSpeedForm.save.data = Camera.save_images

    return render_template('index.html', form = shutterSpeedForm)

@app.route('/changeSettings', methods=['POST'])
def changeSettings():
    print('changeSettings()')
    newSpeed = int(request.form['speed'])
    print(request.form)
    save = (request.form['save'] == 'y') if 'save' in request.form else False
    Camera.update_settings(newSpeed, save)
    return redirect('/')

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    
    cam = Camera()
    cam.start_tracking() #move to being controlled by web page

    return Response(gen(cam),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
