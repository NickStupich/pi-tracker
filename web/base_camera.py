import time
import threading
import cv2
import numpy as np
try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident


from single_point_tracking import SinglePointTracking

class CameraEvent(object):
    """An Event-like class that signals all active clients when a new frame is
    available.
    """
    def __init__(self):
        self.events = {}

    def wait(self, timeout = None):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        if ident not in self.events:
            # this is a new client
            # add an entry for it in the self.events dict
            # each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait(timeout)

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():
                # if this client's event is not set, then set it
                # also update the last set timestamp to now
                event[0].set()
                event[1] = now
            else:
                # if the client's event is already set, it means the client
                # did not process a previous frame
                # if the event stays set for more than 5 seconds, then assume
                # the client is gone and remove it
                if now - event[1] > 5:
                    remove = ident
        if remove:
            del self.events[remove]

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()

class BaseCamera(object):
    thread = None  # background thread that reads frames from camera
    frame = None  # current frame is stored here by background thread
    last_access = 0  # time of last client access to the camera
    event = CameraEvent()
    subimg_event = CameraEvent()

    settings_changed = False
    shutter_speed_ms = 100
    resolution_x = 672
    resolution_y = 496
    save_images = False
    tracking_enabled = False
    restart_tracking = True

    def __init__(self):

        BaseCamera.sub_img = self.get_non_tracking_subimage()
        """Start the background camera thread if it isn't running yet."""
        if BaseCamera.thread is None:
            BaseCamera.last_access = time.time()

            # start background frame thread
            BaseCamera.thread = threading.Thread(target=self._thread)
            BaseCamera.thread.start()

            # wait until frames are available
            while self.get_frame() is None:
                time.sleep(0)

    def get_non_tracking_subimage(self):

        sub_img_half_size = 50
        sub_img = np.ones((sub_img_half_size*2, sub_img_half_size*2), np.uint8) * 128
        return sub_img

    def get_frame(self):
        """Return the current camera frame."""
        BaseCamera.last_access = time.time()

        # wait for a signal from the camera thread
        BaseCamera.event.wait()
        BaseCamera.event.clear()

        frame = BaseCamera.frame

        ret, jpeg = cv2.imencode('.jpg', frame)
        # print('thread to web')

        return jpeg.tobytes()

    def get_subimg_frame(self):
        BaseCamera.subimg_event.wait()
        BaseCamera.subimg_event.clear()
        img = BaseCamera.sub_img
        print('got subimg_frame')
        ret, jpeg = cv2.imencode('.jpg', img)
        return jpeg.tobytes()
    
    def start_tracking(self):
        BaseCamera.restart_tracking = True
        BaseCamera.tracking_enabled = True

    def stop_tracking(self):
        BaseCamera.tracking_enabled = False
        print('stop_tracking()')
        BaseCamera.subimg_event.wait(timeout = 2)
        print('stop_tracking() after')
        BaseCamera.sub_img = self.get_non_tracking_subimage()
        BaseCamera.subimg_event.set()

    @staticmethod
    def frames():
        """"Generator that returns frames from the camera."""
        raise RuntimeError('Must be implemented by subclasses.')

    @classmethod
    def update_settings(cls, speed_ms, save_images):
        print('updating settings')
        BaseCamera.shutter_speed_ms = speed_ms
        BaseCamera.save_images = save_images
        BaseCamera.settings_changed = True


    @classmethod
    def _thread(cls):
        """Camera background thread."""

        tracker = SinglePointTracking()

        print('Starting camera thread.')
        frames_iterator = cls.frames()
        for frame in frames_iterator:
            BaseCamera.frame = frame

            sub_img_half_size = 50
            if BaseCamera.tracking_enabled:
                if not tracker.is_tracking() or BaseCamera.restart_tracking:
                    tracker.restart_tracking(frame)
                    BaseCamera.restart_tracking = False
                else:
                    pos, shift = tracker.process_frame(frame)
                    print('relative position: ', pos)

                    BaseCamera.sub_img = frame[pos[1] - sub_img_half_size:pos[1]+sub_img_half_size, pos[0]-sub_img_half_size:pos[0]+sub_img_half_size]
            
            #even if tracking not enabled we'll broadcast an empty fixed img.
            BaseCamera.subimg_event.set()
            
            BaseCamera.event.set()  # send signal to clients
            time.sleep(0)

            # if there hasn't been any clients asking for frames in
            # the last 10 seconds then stop the thread
            # if time.time() - BaseCamera.last_access > 10 and False:
            #     frames_iterator.close()
            #     print('Stopping camera thread due to inactivity.')
            #     break
                            
        BaseCamera.thread = None
