import numpy as np
import matplotlib.pyplot as plt
import scipy.signal


# https://rppass.com/align.pdf

def sin_deg(x):
    return np.sin(np.deg2rad(x))

def cos_deg(x):
    return np.cos(np.deg2rad(x))

def tan_deg(x):
    return np.tan(np.deg2rad(x))

def test():
    
    if 0: #paper example
        latitude = 42 + 40/60.

        ha1 = 3 / 24 * 360
        dec1 = 48

        ha2 = 23 / 24 * 360
        dec2 = 45

        err_ra = -12  / 60.
        err_dec =  - 21 / 60.
    else:
        ha1, dec1 = -5.698227762442372, 30.138757
        ha2, dec2 = 41.738161225001136, 35.496582
        err_ra, err_dec = -1.8392445381084315, 5.36663824338725
        latitude = 49.3124536

        err_ra = 0

    err_elevation, err_azimuth = get_polar_align_error(ha1, dec1, ha2, dec2, err_ra, err_dec, latitude)

def test_ra_sweep():
    ha1, dec1 = -5.698227762442372, 30.138757
    ha2, dec2 = 41.738161225001136, 35.496582
    # err_ra, err_dec = -1.8392445381084315, 5.36663824338725
    err_ra, err_dec = 0, 5.36663824338725
    latitude = 49.3124536

    err_ra_mag = 2
    err_ras = np.linspace(-err_ra_mag, err_ra_mag, 100)

    err_elevations = []
    err_azimuths = []
    for err_ra in err_ras:
        err_elevation, err_azimuth = get_polar_align_error(ha1, dec1, ha2, dec2, err_ra, err_dec, latitude)
        err_elevations.append(err_elevation)
        err_azimuths.append(err_azimuth)

    # for err_dec in err_ras:
    #     err_elevation, err_azimuth = get_polar_align_error(ha1, dec1, ha2, dec2, err_ra, err_dec, latitude)
    #     err_elevations.append(err_elevation)
    #     err_azimuths.append(err_azimuth)

    plt.subplot(2, 1, 1)
    plt.plot(err_ras, err_elevations)
    # plt.plot(err_ras, scipy.signal.detrend(err_elevations))
    plt.grid(True)
    plt.title('elevation')

    plt.subplot(2, 1, 2)
    plt.plot(err_ras, err_azimuths)
    # plt.plot(err_ras, scipy.signal.detrend(err_azimuths))
    plt.grid(True)
    plt.title('azimuth')

    plt.show()

def get_polar_align_error(ha1, dec1, ha2, dec2, err_ra, err_dec, latitude):
    print('pos1: ', ha1, dec1)
    print('pos2: ', ha2, dec2)
    print('err: ', err_ra, err_dec)
    print('lat: ', latitude)

    d = cos_deg(latitude) * (tan_deg(dec1) + tan_deg(dec2)) * (1 - cos_deg(ha1 - ha2))
    print('determinant: ', d)

    m11 = cos_deg(latitude) * (sin_deg(ha2) - sin_deg(ha1)) / d
    m12 = -cos_deg(latitude) * (tan_deg(dec1) * cos_deg(ha1) - tan_deg(dec2) * cos_deg(ha2)) / d
    m21 = (cos_deg(ha1) - cos_deg(ha2)) / d
    m22 = (tan_deg(dec2) * sin_deg(ha2) - tan_deg(dec1) * sin_deg(ha1)) / d

    err_elevation = m11 * err_ra + m12 * err_dec
    err_azimuth = m21 * err_ra + m22 * err_dec

    print(err_elevation)
    print('arcmins: ', err_elevation * 60 )

    print(err_azimuth)
    print('arcmins: ', err_azimuth * 60)

    return err_elevation, err_azimuth


if __name__ == "__main__":
    # test()
    test_ra_sweep()