import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

sys.path.append('..')
sys.path.append('../web')
from web import single_point_tracking


fx = fy = 0.25
def load_image(filename):
	result = cv2.imread(filename, 0)

	# result = cv2.resize(result, None, fx = 0.25, fy = 0.25)

	return result


def main():
	# folder = "F:/star_guiding/test_frames"
	# folder = "D:/star_guiding/test_frames"
	folder = 'D:/star_guiding/images/2019-02-05.15-27-53'

	# start_position = 	(2914, 2378)

	# start_position = single_point_tracking.get_start_position2(load_image(os.path.join(folder, 'IMG_7955.jpg')))
	# start_position = (201, 694)
	# start_position = (1923, 3040)


	last_position = None#start_position

	all_positions = []

	for i, fn in enumerate(list(os.listdir(folder))[:400]):
		# print(fn)
		full_fn = os.path.join(folder, fn)
		img = load_image(full_fn)
		# print(img.shape)

		if i == 0: 
			last_position = single_point_tracking.get_start_position2(img)

		current_position = single_point_tracking.get_current_star_location(img, last_position, subPixelFit = True)
		# current_position = start_position
		print(current_position)


		if 0:
			current_position_int = (int(current_position[0]), int(current_position[1]))

			n = 50
			sub_img = img[current_position_int[1] - n: current_position_int[1] + n, current_position_int[0] - n:current_position_int[0]+n]
		
		# plt.imshow(img); plt.title(fn); plt.show()
		# plt.imshow(sub_img); plt.title(fn); plt.show()
		
		# plt.imshow(img)
		# plt.show()

		if current_position is not None:
			last_position = current_position

			all_positions.append(current_position)

	all_positions = np.array(all_positions)

	t = np.arange(0, len(all_positions))

	x = t
	y = all_positions[:, 0]
	# y = all_positions[:, 1]

	x = x[40:]
	y = y[40:]

	plt.plot(x, y); plt.grid(True); plt.show()

	fit = np.polyfit(x, y, 3)

	fit_ys = np.poly1d(fit)(x)
	errs = fit_ys - y
	print('error std dev: ', np.std(errs))

	plt.plot(errs); plt.show()


	# plt.scatter(all_positions[:, 0], all_positions[:, 1]); plt.show()

if __name__ == "__main__":
	main()