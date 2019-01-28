import cv2
import numpy as np
#import matplotlib.pyplot as plt

def get_start_position(img, crop_side_fraction = 0.1):
    
    
    crop_x = int(img.shape[1] * crop_side_fraction)
    crop_y = int(img.shape[0] * crop_side_fraction)
    
    cropped_img = img[crop_y:-crop_y, crop_x:-crop_x]
    
    blur_size = 21
    blurred_img = cv2.GaussianBlur(cropped_img, (blur_size, blur_size), 0)

    (minVal, maxVal, minLoc, approxMaxLocCropped) = cv2.minMaxLoc(blurred_img)

    print(approxMaxLocCropped, maxVal)
    approxMaxLoc = (approxMaxLocCropped[0] + crop_x, approxMaxLocCropped[1] + crop_y)

    if 0:
        plt.subplot(1, 2, 1)
        plt.imshow(img)
        plt.subplot(1, 2, 2)
        plt.imshow(blurred_img)
        plt.plot([maxLoc[0]], [maxLoc[1]], 'o')
        plt.show()

    max_loc = get_current_star_location(img, approxMaxLoc)

    return max_loc

def get_start_position2(img, percentile = 90):
    threshold_value = np.percentile(img, percentile)
    # print('threshold: ', threshold_value)
    ret, stars_img = cv2.threshold(img, threshold_value, 255, cv2.THRESH_BINARY)

    stars_img_adaptive = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, -threshold_value) / 255

    img_masked = img * stars_img_adaptive
    result = get_start_position(img_masked)
    return result

def get_current_star_location(img, last_position, search_half_size = 50):
    blur_size = 11
    
    if last_position[0] < search_half_size or last_position[1] < search_half_size or last_position[1] > (img.shape[0] - search_half_size - 1) or last_position[0] > (img.shape[1] - search_half_size - 1):
        return None
    
    print('last position: ', last_position)
    sub_img = img[int(last_position[1]) - search_half_size:int(last_position[1]) + search_half_size, int(last_position[0]) - search_half_size : int(last_position[0]) + search_half_size]
    blurred_sub_img = cv2.GaussianBlur(sub_img, (blur_size, blur_size), 0)

    max_loc = np.argmax(blurred_sub_img)
    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(blurred_sub_img)

    #todo: refine this
    current_position = (maxLoc[0] + (last_position[0] - search_half_size), maxLoc[1] + (last_position[1] - search_half_size))

    return current_position

class SinglePointTracking():
    last_coords = None
    _is_tracking = False
    failed_track_count = 0

    all_coords = []

    def __init__(self, search_img_half_size):
        print('created tracker object')
        self.search_img_half_size = search_img_half_size

    def restart_tracking(self, base_frame, starting_coords = None):
        print('start tracking()')
        self.all_coords = []
        self.base_frame = base_frame

        #if starting_coords is None:
        self.starting_coords = get_start_position2(base_frame)
        print('starting coords: ', self.starting_coords)

        if self.starting_coords is None:
            return False

        self.last_coords = self.starting_coords
        self._is_tracking = True

    def is_tracking(self):
        return self._is_tracking

    def process_frame(self, new_frame):
        current_location = get_current_star_location(new_frame, self.last_coords, self.search_img_half_size)
        if current_location is None:
            self.failed_track_count += 1
            print('failed track count: ', self.failed_track_count)
        
            
            return self.last_coords, None
        


        self.failed_track_count = 0
            
        
        # print(current_location, self.last_coords)
        self.last_coords = current_location
        shift = (current_location[0] - self.starting_coords[0], current_location[1] - self.starting_coords[1])
        self.all_coords.append(current_location)
        return current_location, shift

    def overlay_tracking_information(self, frame, overlay_tracking_history = False, overlay_color = (255,)):
        n = self.search_img_half_size
        cv2.rectangle(frame, (self.last_coords[0] - n, self.last_coords[1] - n), (self.last_coords[0] + n, self.last_coords[1] + n), overlay_color)
        
        if overlay_tracking_history:
            for i in range(1, len(self.all_coords)):
                cv2.line(frame, self.all_coords[i-1], self.all_coords[i], overlay_color)
