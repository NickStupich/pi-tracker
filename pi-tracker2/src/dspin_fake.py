
from dspin_constants import *

def dspin_Run(dir, speed):
	print('dspin run: ', int(speed))

def dspin_SpdCalc(stepsPerSec):
	result = stepsPerSec * 67.106
	if result > 0x3FFF:
		result = 0x3FFF
	# print('speed result: ', int(result))
	return result

def dspin_SoftStop():
	print('dspin softstop')

def connect_l6470():
	print('dspin connecting...')

def disconnect_l6470():
	print('dspin disconnecting...')
