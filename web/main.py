#!/usr/bin/env python

from flask import Flask, render_template, Response, request, redirect
# from flask_wtf import FlaskForm
from wtforms import Form, StringField, TextField, validators, IntegerField, FloatField

import webcam
# import picam
import files_cam


#cam = webcam.VideoCamera()
# cam = picam.VideoCamera()
cam = files_cam.VideoCamera()
print('MADE NEW CAM')

app = Flask(__name__)

class ShutterSpeedForm(Form):
    speed = IntegerField('Shutter Speed:', validators=[validators.required()])
    


@app.route('/', methods=['GET', 'POST'])
def index():
    shutterSpeedForm = ShutterSpeedForm()
    shutterSpeedForm.speed.data = cam.getShutterMicroseconds()

    return render_template('index.html', form = shutterSpeedForm)
    
@app.route('/updateShutterSpeed', methods=['POST'])
def updateSpeed():
    newSpeed = request.form['speed']
    print('setting new speed: ', newSpeed)
    newSpeedFloat = float(newSpeed)
    cam.setShutterMicroseconds(newSpeedFloat)

    return redirect('/')


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(cam),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)