
import time
import threading
from datetime import datetime

class CameraAdjuster(object):
    thread = None
    camera = None
    
    restartAdjusting = False
    stopAdjusting = False
    isRunning = False
    
    def __init__(self, camera = None):
        if CameraAdjuster.camera is None:
            CameraAdjuster.camera = camera
            
        if CameraAdjuster.thread is None:
            #print('thread is none')
            CameraAdjuster.thread = threading.Thread(target=self._thread)
            CameraAdjuster.thread.start()
            
    def start_following(self):        
        print('start following')
        restartAdjusting = True
        
    def stop_following(self):
        print('stop following')
        stopAdjusting = True
            
    @classmethod
    def _restartAdjusting(cls):
        restartAdjusting = False
        
        start_frame = CameraAdjuster.camera.get_frame()
        while 1:
            if restartAdjusting or stopAdjusting:
                break
            
            
            
            
    @classmethod
    def _runAdjustments(cls):
        pass
    
    
            
    @classmethod
    def _thread(cls):
        while(1):
            time.sleep(1)
        