import time
from base_camera import BaseCamera
import os
import cv2

class Camera(BaseCamera):
    """An emulated camera implementation that streams a repeated sequence of
    files 1.jpg, 2.jpg and 3.jpg at a rate of one frame per second."""
    # imgs = [open(f + '.jpg', 'rb').read() for f in ['1', '2', '3']]


    @staticmethod
    def frames():

        folder = 'F:/star_guiding/test_frames'
        filenames = list(filter(lambda s: s.startswith('IMG'), os.listdir(folder)))[:5]
        imgs = [cv2.imread(os.path.join(folder, file), 0) for file in filenames]
        # print(len(imgs), imgs[0].shape)
        count = 0
        while True:
            time.sleep(1)
            # yield Camera.imgs[int(time.time()) % 3]
            index = count % len(imgs)
            if (count // len(imgs)) % 2 > 0: #flip around backwards for continuity
                index = len(imgs) - index - 1
            # print(count, len(imgs), index)

            img = imgs[index]
            count += 1

            ret, jpg = cv2.imencode('.jpg', img)
            # print(img.shape, img.dtype, jpg.shape)
            yield jpg.tobytes()
