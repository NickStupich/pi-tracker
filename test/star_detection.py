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
	# folder = 'F:/star_guiding/images/2019-02-05.15-27-53'

	# start_position = 	(2914, 2378)

	# start_position = single_point_tracking.get_start_position2(load_image(os.path.join(folder, 'IMG_7955.jpg')))
	# start_position = (201, 694)
	# start_position = (1923, 3040)


	last_position = None#start_position

	all_positions = []
	t = []

	files = list(sorted(os.listdir(folder), key = lambda s: int(s.split('.')[0])))
	# print(files)

	# print(os.listdir(folder)[4278])

	for i, fn in enumerate(files[500:]):
		if i > 4000: break
		# print(fn)
		full_fn = os.path.join(folder, fn)
		img = load_image(full_fn)
		# print(img.shape)

		if i == 0: 
			last_position = single_point_tracking.get_start_position2(img)

		current_position = single_point_tracking.get_current_star_location(img, last_position, subPixelFit = False)
		# current_position = start_position
		# print(i, current_position)


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
			t.append(i)
		else:
			# all_positions.append((-1, -1))
			pass


	all_positions = np.array(all_positions)

	plt.subplot(1, 2, 1)
	plt.plot(t, all_positions[:, 0], '--.')
	plt.title('x')

	plt.subplot(1, 2, 2)
	plt.plot(t, all_positions[:, 1], '--.')
	plt.title('y')

	plt.show()

	if 1:

		fit_x = np.polyfit(t, all_positions[:, 0], 2)
		plt.subplot(1, 2, 1)
		plt.plot(t, all_positions[:, 0] - np.poly1d(fit_x)(t), '--.')
		plt.title('x')

		fit_y = np.polyfit(t, all_positions[:, 1], 2)
		plt.subplot(1, 2, 2)
		plt.plot(t, all_positions[:, 1] - np.poly1d(fit_y)(t), '--.')
		plt.title('y')

		plt.show()

	# x = t
	# y = all_positions[:, 0]
	# y = all_positions[:, 1]

	# x = x[40:]
	# y = y[40:]

	# plt.plot(x, y); plt.grid(True); plt.show()




	# fit = np.polyfit(x, y, 3)

	# fit_ys = np.poly1d(fit)(x)
	# errs = fit_ys - y
	# print('error std dev: ', np.std(errs))

	# plt.plot(errs); plt.show()


	# plt.scatter(all_positions[:, 0], all_positions[:, 1]); plt.show()


def get_mean_plot():
	# folder = "F:/star_guiding/test_frames"
	# folder = "D:/star_guiding/test_frames"
	folder = 'D:/star_guiding/images/2019-02-05.15-27-53'
	# folder = 'F:/star_guiding/images/2019-02-05.15-27-53'

	ref_position = (860, 445)
	last_position = None#start_position

	all_positions = []
	t = []

	aligned_images = []

	files = list(sorted(os.listdir(folder), key = lambda s: int(s.split('.')[0])))

	for i, fn in enumerate(files[500:]):
		if i > 800: break
		full_fn = os.path.join(folder, fn)
		img = load_image(full_fn)

		if i == 0: 
			last_position = single_point_tracking.get_start_position2(img)
 	 	
		current_position = single_point_tracking.get_current_star_location(img, last_position, subPixelFit = False)

		if current_position is not None:
			dx = ref_position[0] - current_position[0]
			dy = ref_position[1] - current_position[1]

			M = np.float32([[1,0,dx],[0,1,dy]])
			dst = cv2.warpAffine(img,M,img.shape[::-1])
			aligned_images.append(dst)

		# plt.subplot(1, 2, 1)
		# plt.imshow(img)
		# plt.subplot(1, 2, 2)
		# plt.imshow(dst)
		# plt.show()

		if current_position is not None:
			last_position = current_position

			all_positions.append(current_position)
			t.append(i)
		else:
			# all_positions.append((-1, -1))
			pass


	aligned_images = np.array(aligned_images)

	mean_image = np.mean(aligned_images, axis=0)
	plt.imshow(np.clip(mean_image * 10, 0, 1)); plt.show()

if __name__ == "__main__":
	# main()
	get_mean_plot()