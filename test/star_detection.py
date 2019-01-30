import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

sys.path.append('..')
from web import single_point_tracking


fx = fy = 0.25
def load_image(filename):
	result = cv2.imread(filename, 0)

	result = cv2.resize(result, None, fx = 0.25, fy = 0.25)

	return result


def main():
	folder = "F:/star_guiding/test_frames"

	# start_position = 	(2914, 2378)

	start_position = single_point_tracking.get_start_position2(load_image(os.path.join(folder, 'IMG_7955.jpg')))


	last_position = start_position

	all_positions = []

	for fn in filter(lambda s: s.startswith('IMG'), os.listdir(folder)):#[:10]:
		# print(fn)
		full_fn = os.path.join(folder, fn)
		img = load_image(full_fn)
		# print(img.shape)

		current_position = single_point_tracking.get_current_star_location(img, last_position)
		# current_position = start_position
		print(current_position)
		n = 50
		sub_img = img[current_position[1] - n: current_position[1] + n, current_position[0] - n:current_position[0]+n]
		plt.imshow(sub_img); plt.title(fn); plt.show()
		
		# plt.imshow(img)
		# plt.show()


		last_position = current_position

		all_positions.append(current_position)

	all_positions = np.array(all_positions)


	fit = np.polyfit(all_positions[:, 0], all_positions[:, 1], 1)

	fit_ys = np.poly1d(fit)(all_positions[:, 0])
	errs = fit_ys - all_positions[:, 1]
	print('error std dev: ', np.std(errs))

	plt.plot(errs); plt.show()


	# plt.scatter(all_positions[:, 0], all_positions[:, 1]); plt.show()

if __name__ == "__main__":
	main()