import cv2
import numpy as np
import scipy.optimize
from datetime import datetime
import threading

import redis_helpers
import redis
import messages

def get_start_position(img, crop_side_fraction = 0.1):
    
    
    crop_x = int(img.shape[1] * crop_side_fraction)
    crop_y = int(img.shape[0] * crop_side_fraction)
    
    cropped_img = img[crop_y:-crop_y, crop_x:-crop_x]
    
    blur_size = 21
    blurred_img = cv2.GaussianBlur(cropped_img, (blur_size, blur_size), 0)

    (minVal, maxVal, minLoc, approxMaxLocCropped) = cv2.minMaxLoc(blurred_img)

    # print(approxMaxLocCropped, maxVal)
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
    ret, stars_img = cv2.threshold(img, threshold_value, 255, cv2.THRESH_BINARY)

    stars_img_adaptive = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, -threshold_value) / 255

    img_masked = img * stars_img_adaptive
    result = get_start_position(img_masked)
    return result

ema_num = 0
ema_denom = 0
def get_current_star_location(img, last_position, search_half_size = 50, subPixelFit = True, ema_smoothing = None):
    blur_size = 11
    if last_position[0] < search_half_size or last_position[1] < search_half_size or last_position[1] > (img.shape[0] - search_half_size - 1) or last_position[0] > (img.shape[1] - search_half_size - 1):
        return None
    
    sub_img = img[int(last_position[1]) - search_half_size:int(last_position[1]) + search_half_size, int(last_position[0]) - search_half_size : int(last_position[0]) + search_half_size]
    blurred_sub_img = cv2.GaussianBlur(sub_img, (blur_size, blur_size), 0)

    max_loc = np.argmax(blurred_sub_img)
    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(blurred_sub_img)
    
    changeLimitPixels = 20
    if abs(maxLoc[0] - search_half_size) > changeLimitPixels or abs(maxLoc[1] - search_half_size) > changeLimitPixels:
       return None

    if subPixelFit:
        try:
            subPixelMaxLoc = improve_star_location_gaussian_fit(blurred_sub_img, maxLoc)

            subPixelMoveLimit = 5

            if abs(subPixelMaxLoc[0] - maxLoc[0]) > subPixelMoveLimit or abs(subPixelMaxLoc[1] - maxLoc[1]) > subPixelMoveLimit:
                print('sub pixel fitting moved too far: ', maxLoc, subPixelMaxLoc)

            else:
                maxLoc = subPixelMaxLoc
        except RuntimeError as re:
            pass

        except Exception as e:
            print(e)


    if ema_smoothing:
        global ema_num, ema_denom
        ema_num = ema_num * (1 - ema_smoothing) + ema_smoothing * np.array(maxLoc)
        ema_denom = ema_denom * (1 - ema_smoothing) + ema_smoothing

        maxLoc = ema_num / ema_denom

    #todo: refine this
    current_position = (maxLoc[0] + (last_position[0] - search_half_size), maxLoc[1] + (last_position[1] - search_half_size))

    return current_position

def improve_star_location_gaussian_fit(img, position):

    size_pixels = 5

    position_int = (int(position[0]), int(position[1]))

    x = np.linspace(position_int[0] - size_pixels, position_int[0] + size_pixels, size_pixels*2 )
    y = np.linspace(position_int[1] - size_pixels, position_int[1] + size_pixels, size_pixels*2 )
    x, y = np.meshgrid(x, y)

    sub_img = img[position_int[1] - size_pixels: position_int[1] + size_pixels, position_int[0] - size_pixels: position_int[0] + size_pixels]

    xy = np.vstack((x, y))

    initial_guess = (255, position[0], position[1], 1, 0)#np.mean(sub_img))
    guess_plot = twoD_Gaussian((x, y), *initial_guess)

    popt, pcov = scipy.optimize.curve_fit(twoD_Gaussian, (x, y), sub_img.ravel(), p0=initial_guess)
    
    data_fitted = twoD_Gaussian((x, y), *popt)

    if 0: 
        plt.subplot(1, 2, 1)
        plt.imshow(sub_img)
        plt.contour(data_fitted.reshape(x.shape), 8)
        plt.subplot(1, 2, 2)
        plt.imshow(guess_plot.reshape(sub_img.shape))
        plt.show() 

    new_pos = (popt[1], popt[2])

    return new_pos

def twoD_Gaussian(locs, amplitude, xo, yo, sigma, offset):
    x, y = locs                                                 
    xo = float(xo)                                                              
    yo = float(yo)            
    g = offset + amplitude * np.exp(-sigma * ((x-xo)**2 + (y-yo)**2))
    return g.ravel()

class SinglePointTracking(threading.Thread):
    last_coords = None
    is_tracking = False
    starting_coords = None
    
    shift_update_time = None
    shift_x = None
    shift_y = None

    def __init__(self, search_img_half_size=50):
        threading.Thread.__init__(self)
        print('created tracker object')
        self.search_img_half_size = search_img_half_size
        self.non_tracking_sub_image_serialized = redis_helpers.toRedis(
                                            np.ones((2*self.search_img_half_size, 2*self.search_img_half_size), 
                                                dtype=np.uint8) * 128
                                            )

    def run(self):
        self.r = redis.StrictRedis(host='localhost', port=6379) 
        p = self.r.pubsub(ignore_subscribe_messages=True)

        p.subscribe(messages.STOP_ALL)
        p.subscribe(messages.CMD_START_TRACKING)
        p.subscribe(messages.CMD_STOP_TRACKING)
        p.subscribe(messages.NEW_IMAGE_FRAME)

        while 1:
            message = p.get_message()
            if message:
                channel = message['channel'].decode('ASCII')
                data = message['data']

                if channel == messages.STOP_ALL:
                    break
                elif channel == messages.CMD_START_TRACKING:
                    self.last_coords = None
                    self.is_tracking = True
                elif channel == messages.CMD_STOP_TRACKING:
                    self.is_tracking = False
                elif channel == messages.NEW_IMAGE_FRAME:
                    if self.is_tracking:
                        img = redis_helpers.fromRedis(data)
                        self.process_frame(img)
                        if self.last_coords is None:
                            self.r.publish(messages.NEW_SUB_IMAGE_FRAME, self.non_tracking_sub_image_serialized)
                        else:
                            sub_img = img[int(self.last_coords[1]) - self.search_img_half_size:int(self.last_coords[1]) + self.search_img_half_size, 
                            int(self.last_coords[0]) - self.search_img_half_size : int(self.last_coords[0]) + self.search_img_half_size]
                            self.r.publish(messages.NEW_SUB_IMAGE_FRAME, 
                                redis_helpers.toRedis(sub_img))
    
                    else:
                        self.r.publish(messages.NEW_SUB_IMAGE_FRAME, self.non_tracking_sub_image_serialized)

    def process_frame(self, new_frame, subPixelFit = True):
        if self.last_coords is None:
            self.last_coords = get_start_position2(new_frame)
            if self.last_coords is not None:
                self.r.publish(messages.STATUS_STARTING_TRACKING_POSITION, redis_helpers.toRedis(self.last_coords))
        else:
            current_location = get_current_star_location(new_frame, self.last_coords, self.search_img_half_size, subPixelFit = subPixelFit)
            if current_location is None:
                return
            
            n = self.search_img_half_size
            
            valid = current_location is not None \
                and current_location[0] > n \
                and current_location[1] > n \
                and current_location[0] < new_frame.shape[1] - n \
                and current_location[1] < new_frame.shape[0] - n
            
            if valid:
                self.last_coords = current_location
                self.r.publish(messages.STATUS_CURRENT_TRACKING_POSITION, redis_helpers.toRedis(current_location))
        
        # self.last_coords = current_location
        # shift = (current_location[0] - self.starting_coords[0], current_location[1] - self.starting_coords[1])
        # self.shift_x = shift[0]
        # self.shift_y = shift[1]
        # self.shift_update_time = datetime.now()
        # self.all_coords.append(current_location)
        # return current_location, shift

    def overlay_tracking_information(self, frame, overlay_tracking_history = False, overlay_color = (255,)):
        n = self.search_img_half_size
        
        valid = self.last_coords is not None \
            and self.last_coords[0] > n \
            and self.last_coords[1] > n \
            and self.last_coords[0] < frame.shape[1] - n \
            and self.last_coords[1] < frame.shape[0] - n
        
        if valid:
            #print(frame.shape, frame.dtype)
            cv2.rectangle(frame, (int(self.last_coords[0]) - n, int(self.last_coords[1]) - n), (int(self.last_coords[0]) + n, int(self.last_coords[1]) + n), overlay_color)
        
        if overlay_tracking_history:
            for i in range(1, len(self.all_coords)):
                cv2.line(frame, (int(self.all_coords[i-1][0]), int(self.all_coords[i-1][1])), (int(self.all_coords[i][0]), int(self.all_coords[i][1])), overlay_color)
