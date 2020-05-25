
import imageio

import rawpy
import gphoto2 as gp
import subprocess
import time
import os
import matplotlib.pyplot as plt
import numpy as np

from astropy.stats import sigma_clipped_stats
from photutils import DAOStarFinder, find_peaks

from astropy.modeling import models, fitting

def fit_single_star(img, x, y, peak_value = 1):

    box = 21
    fit_p = fitting.LevMarLSQFitter()

    # int_x = int(x)
    # int_y = int(y)

    # sub_img = img[int_y - half_size:int_y + half_size +1, int_x - half_size:int_x + half_size+1]

    if 0:
        plt.imshow(sub_img)
        plt.show()


    # model = models.Gaussian2D(x_mean=half_size, y_mean=half_size, x_stddev=5, y_stddev=5)
    model = models.Gaussian2D(x_mean=x, y_mean=y, x_stddev=1, y_stddev=1)
    model.amplitude = peak_value

    # Establish reasonable bounds for the fitted parameters
    model.x_stddev.bounds = (0, 7)
    model.y_stddev.bounds = (0, 7)
    model.x_mean.bounds = (x - 5, x + 5)
    model.y_mean.bounds = (y - 5, y + 5)

    # np.mgrid[int(xmin):int(xmax), int(ymin):int(ymax)]
    leny, lenx = img.shape
    xmin, xmax = max(x-box/2, 0), min(x+box/2+1, lenx-1)
    ymin, ymax = max(y-box/2, 0), min(y+box/2+1, leny-1)
    # print(x, xmin, xmax, y, ymin, ymax)
    xgrid, ygrid = np.mgrid[int(xmin):int(xmax), int(ymin):int(ymax)]
    # print(x, xgrid)
    sub_img = img[ygrid, xgrid]
    sub_img -= np.median(sub_img)

    # print(xgrid.shape, ygrid.shape, sub_img.shape)

    p = fit_p(model, xgrid, ygrid, sub_img)
    # print(p)

    if 0:
        plt.imshow(sub_img)
        plt.show()


    # x_std = p['x_stddev']
    # y_std = p['y_stddev']

    x_std = p.x_stddev
    y_std = p.y_stddev

    x_fwhm = 2.3548 * x_std
    y_fwhm = 2.3548 * y_std

    return x_fwhm, y_fwhm


def test_fwhm_calc():

    # img_fn = '/media/sf_ubuntu/2020-05-14_22-55-10/good/0.ARW'
    img_fn = '/media/sf_ubuntu/focus_test/DSC02191.ARW'

    calc_fwhm(img_fn)

def calc_fwhm(img_fn):

    raw_img = rawpy.imread(img_fn)
    img_rgb = np.mean(raw_img.postprocess(no_auto_bright=True, output_bps=16, half_size=False), axis=2)

    img = img_rgb.astype('float32') / (2**14)
    img = img[1500:2500, 2500:3500]

    print(img.shape)

    # img_median = np.median(img)
    mean, median, std = sigma_clipped_stats(img, sigma=3)

    daofind = DAOStarFinder(fwhm=5.0, threshold=5*std)

    if 0:
        sources = daofind(img - median)
        for col in sources.colnames:  
            sources[col].info.format = '%.3g'  # for consistent table output

        print(sources)
    else:
        stars = find_peaks(img - median, threshold = 5*std, box_size = 11)
        print(stars)

    if 0:
        plt.imshow(img)
        plt.show()


    fwhms = []
    positions = []

    for i in range(len(stars)):
        star = stars[i]

        x = star['x_peak']
        y = star['y_peak']
        peak_value = star['peak_value']

        if peak_value < 0.5: continue

        # print(star)
        fwhm_x, fwhm_y = fit_single_star(img, x, y, peak_value)

        fwhms.append((fwhm_x, fwhm_y))
        positions.append((x, y))


    values = np.array(fwhms)
    overall_fwhm = np.median(values)
    print('overall fwhm: ', overall_fwhm)

    if 0:
        grid_x, grid_y = np.mgrid[0:img.shape[1], 0:img.shape[0]]
        points = np.array(positions)

        from scipy.interpolate import griddata

        grid_fwhm = griddata(points, values, (grid_x, grid_y), method='linear')
        # print(grid_fwhm.shape)

        plt.subplot(2, 1, 1)
        plt.imshow(grid_fwhm[:, :, 0])
        plt.title('x')
        plt.subplot(2, 1, 2)
        plt.imshow(grid_fwhm[:, :, 1])
        plt.title('y')
        plt.show()

    return overall_fwhm

def test_focus_sweep():

    camera = gp.Camera()
    camera.init()
    
    config = camera.get_config()
    OK, bulb_child = gp.gp_widget_get_child_by_name(config, 'bulb')

if __name__ == "__main__":
    # test_fwhm_calc()

    test_focus_sweep()