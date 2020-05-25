import numpy as np

# https://rppass.com/align.pdf

def sin_deg(x):
    return np.sin(np.deg2rad(x))

def cos_deg(x):
    return np.cos(np.deg2rad(x))

def tan_deg(x):
    return np.tan(np.deg2rad(x))

def test():
    
    latitude = 42 + 40/60.

    ha1 = 3 / 24 * 360
    dec1 = 48

    ha2 = 23 / 24 * 360
    dec2 = 45

    err_ra = -12  / 60.
    err_dec =  - 21 / 60.


    d = cos_deg(latitude) * (tan_deg(dec1) + tan_deg(dec2)) * (1 - cos_deg(ha1 - ha2))

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


if __name__ == "__main__":
    test()