
from dspin_constants import *

def dspin_Run(dir, speed):
	print('dspin run: ', speed)

def dspin_SpdCalc(stepsPerSec):
	result = stepsPerSec * 67.106
	if result > 0x3FFF:
		result = 0x3FFF
	# print('speed result: ', int(result))
	return int(result)

def connect_l6470():
	print('dspin connecting...')

def disconnect_l6470():
	print('dspin disconnecting...')
