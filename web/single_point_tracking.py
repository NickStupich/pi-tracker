import cv2
import numpy as np
import scipy.optimize

import is_pi

if not is_pi.is_pi:
    import matplotlib.pyplot as plt

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
    
    # print('last position: ', last_position)
    sub_img = img[int(last_position[1]) - search_half_size:int(last_position[1]) + search_half_size, int(last_position[0]) - search_half_size : int(last_position[0]) + search_half_size]
    blurred_sub_img = cv2.GaussianBlur(sub_img, (blur_size, blur_size), 0)

    max_loc = np.argmax(blurred_sub_img)
    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(blurred_sub_img)

    # plt.imshow(sub_img); plt.scatter([maxLoc[0]], [maxLoc[1]]); plt.show()

    if 1:
        # maxLoc = improve_star_location_gaussian_fit(sub_img, maxLoc)
        maxLoc = improve_star_location_gaussian_fit(blurred_sub_img, maxLoc)

    #todo: refine this
    current_position = (maxLoc[0] + (last_position[0] - search_half_size), maxLoc[1] + (last_position[1] - search_half_size))


    return current_position

def improve_star_location_gaussian_fit(img, position):

    size_pixels = 5

    position_int = (int(position[0]), int(position[1]))

    x = np.linspace(position_int[0] - size_pixels, position_int[0] + size_pixels, size_pixels*2 )
    y = np.linspace(position_int[1] - size_pixels, position_int[1] + size_pixels, size_pixels*2 )
    # print(x)
    x, y = np.meshgrid(x, y)

    # sub_img = img[position_int[0] - size_pixels: position_int[0] + size_pixels, position_int[1] - size_pixels: position_int[1] + size_pixels]
    sub_img = img[position_int[1] - size_pixels: position_int[1] + size_pixels, position_int[0] - size_pixels: position_int[0] + size_pixels]

    # print(x.shape, y.shape, sub_img.shape)

    xy = np.vstack((x, y))

    initial_guess = (255, position[0], position[1], 1, 0)#np.mean(sub_img))
    guess_plot = twoD_Gaussian((x, y), *initial_guess)
    # print(guess_plot.shape)

    # plt.plot(sub_img.ravel()); plt.plot(guess_plot); plt.show() 

    popt, pcov = scipy.optimize.curve_fit(twoD_Gaussian, (x, y), sub_img.ravel(), p0=initial_guess)


    data_fitted = twoD_Gaussian((x, y), *popt)
    # print(data_fitted.shape) 

    if 0: 
        plt.subplot(1, 2, 1)
        plt.imshow(sub_img)
        plt.contour(data_fitted.reshape(x.shape), 8)
        plt.subplot(1, 2, 2)
        plt.imshow(guess_plot.reshape(sub_img.shape))
        plt.show() 


    # print(popt, initial_guess)

    # plt.imshow(sub_img); 
    # plt.imshow(twoD_Gaussian((x, y), *popt).reshape(sub_img.shape)); plt.show()

    new_pos = (popt[1], popt[2])
    print(position, new_pos)
    # exit(0)

    return new_pos


def twoD_Gaussian(locs, amplitude, xo, yo, sigma, offset):
    x, y = locs                                                 
    xo = float(xo)                                                              
    yo = float(yo)            
    g = offset + amplitude * np.exp(-sigma * ((x-xo)**2 + (y-yo)**2))
    # print(g.shape, g.ravel().shape)
    # return g
    return g.ravel()

    # xo = float(xo)
    # yo = float(yo)    
    # a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
    # b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
    # c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
    # g = offset + amplitude*np.exp( - (a*((x-xo)**2) + 2*b*(x-xo)*(y-yo) 
    #                         + c*((y-yo)**2)))
    # return g.ravel()


class SinglePointTracking():
    last_coords = None
    _is_tracking = False
    
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
            
            return self.last_coords, None
        
        # print(current_location, self.last_coords)
        self.last_coords = current_location
        shift = (current_location[0] - self.starting_coords[0], current_location[1] - self.starting_coords[1])
        self.all_coords.append(current_location)
        return current_location, shift

    def overlay_tracking_information(self, frame, overlay_tracking_history = False, overlay_color = (255,)):
        n = self.search_img_half_size
        cv2.rectangle(frame, (int(self.last_coords[0]) - n, int(self.last_coords[1]) - n), (int(self.last_coords[0]) + n, int(self.last_coords[1]) + n), overlay_color)
        
        if overlay_tracking_history:
            for i in range(1, len(self.all_coords)):
                cv2.line(frame, (int(self.all_coords[i-1][0]), int(self.all_coords[i-1][1])), (int(self.all_coords[i][0]), int(self.all_coords[i][1])), overlay_color)
