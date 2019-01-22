import picam
import cv2
import numpy as np


cam = picam.VideoCamera()

while 1:
    #dst = np.empty(cam.cam.resolution, dtype=np.uint8)
    img_bytes = cam.get_frame()
    print(type(img_bytes))
    img = cv2.imdecode(img_bytes, 0)
    print(img.shape)