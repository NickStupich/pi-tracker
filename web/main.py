#!/usr/bin/env python

from flask import Flask, render_template, Response, request, redirect
# from flask_wtf import FlaskForm
from wtforms import Form, StringField, TextField, validators, IntegerField, FloatField

import webcam
import picam
import files_cam

cam = None

app = Flask(__name__)

class ShutterSpeedForm(Form):
    speed = IntegerField('Shutter Speed:', validators=[validators.required()])
    
class SaveEnabledForm(Form):
    save = IntegerField('Save Images: ')

@app.route('/', methods=['GET', 'POST'])
def index():
    print('index')
    save = int(request.args.get('save', '0'))
    shutterSpeed = int(request.args.get('shutter', str(cam.getShutterMicroseconds())))

    cam.setShutterMicroseconds(shutterSpeed)
    cam.setSavingEnabled(save)

    return render_template('index.html')
    
@app.route('/updateShutterSpeed', methods=['POST'])
def updateSpeed():
    print('starting to update shutter speed')
    newSpeed = request.form['speed']
    print('setting new speed: ', newSpeed)
    newSpeedFloat = int(newSpeed)
    cam.setShutterMicroseconds(newSpeedFloat)

    return redirect('/')

@app.route('/updateSavingEnabled', methods=['POST'])
def updateSaving():
    saveEnabled = request.form['save']
    print('setting saving to: ', saveEnabled)
    cam.setSavingEnabled(saveEnabled)
    return redirect('/')

def gen(camera):
    while True:
        frame = camera.get_frame()
        #print(type(frame))
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(cam),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    if cam is None:
        print('MAKING NEW CAM')
        #cam = webcam.VideoCamera()
        cam = picam.VideoCamera()
        # cam = files_cam.VideoCamera()
        print('MADE NEW CAM')
    app.run(host='0.0.0.0', debug=False)
