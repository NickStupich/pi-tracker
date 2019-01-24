import cv2
import numpy as np
import matplotlib.pyplot as plt

def get_start_position(img):
	blur_size = 21
	blurred_img = cv2.GaussianBlur(img, (blur_size, blur_size), 0)

	(minVal, maxVal, minLoc, approxMaxLoc) = cv2.minMaxLoc(blurred_img)

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

	# plt.imshow(img_masked); plt.show()

	result = get_start_position(img_masked)
	return result


half_range = 50
blur_size = 11
def get_current_star_location(img, last_position):

	global half_range
	global blur_size

	sub_img = img[int(last_position[1]) - half_range:int(last_position[1]) + half_range, int(last_position[0]) - half_range : int(last_position[0]) + half_range]
	blurred_sub_img = cv2.GaussianBlur(sub_img, (blur_size, blur_size), 0)

	max_loc = np.argmax(blurred_sub_img)
	(minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(blurred_sub_img)
	# print(maxLoc)
	# plt.imshow(sub_img); plt.show()
	# plt.imshow(blurred_sub_img); plt.plot([maxLoc[0]], [maxLoc[1]], 'or'); plt.show()


	#todo: refine this
	current_position = (maxLoc[0] + (last_position[0] - half_range), maxLoc[1] + (last_position[1] - half_range))

	return current_position

class SinglePointTracking():
	last_coords = None
	_is_tracking = False

	def __init__(self):
		print('created tracker object')

	def start_tracking(self, base_frame, starting_coords = None):
		print('start tracking()')

		self.base_frame = base_frame

		if starting_coords is None:
			self.starting_coords = get_start_position2(base_frame)
			print('starting coords: ', self.starting_coords)

		self.last_coords = self.starting_coords
		self._is_tracking = True

	def is_tracking(self):
		return self._is_tracking

	def process_frame(self, new_frame):
		current_location = get_current_star_location(new_frame, self.last_coords)
		# print(current_location, self.last_coords)
		self.last_coords = current_location
		shift = (current_location[0] - self.starting_coords[0], current_location[1] - self.starting_coords[1])
		return shift