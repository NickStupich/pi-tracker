from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation
from astropy.time import Time
import datetime
import numpy as np

home_location = EarthLocation(lat='49.3118d', lon='-123.0773d')
# home_location = ('49.3118d', '123.0773d')

def degrees_to_hms(d):
	hours = int(d // (360/24))
	mins_decimal = (d/15 - hours) * 60
	mins = int(np.floor(mins_decimal))
	secs = (mins_decimal - mins) * 60

	return hours, mins, secs

def degrees_to_dms(d):
	degrees = int(np.floor(d))
	arcmins_decimal = (d - degrees) * 60
	arcmins = int(np.floor(arcmins_decimal))
	arcsecs = (arcmins_decimal - arcmins) * 60

	return degrees, arcmins, arcsecs

if __name__ == "__main__":
	t = Time(datetime.datetime.utcnow(), scale='utc', location=home_location)
	# t = Time(datetime.datetime.now(), scale='utc', location=home_location)
	print(t)
	t.delta_ut1_utc = 0

	test_ra = 18*15 + 36*15/60 + 57*15/3600
	test_dec = 38 + 47/60. + 8 / 3600.

	test_ha = t.sidereal_time('mean').degree - test_ra
	if test_ha < 0: test_ha += 360

	print('sidereal time: ', t.sidereal_time('mean').degree)
	print('sidereal time: ', degrees_to_hms(t.sidereal_time('mean').degree))

	print('ra, dec: ', test_ra, test_dec)
	print('ra, dec: ', degrees_to_hms(test_ra), degrees_to_dms(test_dec))
	print('ha, dec: ', test_ha, test_dec)
	print('ha, dec: ', degrees_to_hms(test_ha), degrees_to_dms(test_dec))

