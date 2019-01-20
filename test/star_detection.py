import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

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

def main():
	folder = "D:/astro_exports/star_guiding/test_frames"

	start_position = 	(2914, 2378)

	last_position = start_position

	all_positions = []

	for fn in os.listdir(folder):#[:10]:
		full_fn = os.path.join(folder, fn)
		img = cv2.imread(full_fn, 0)
		# print(img.shape)

		current_position = get_current_star_location(img, last_position)

		print(current_position)


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