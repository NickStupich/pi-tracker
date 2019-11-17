import spidev
import time
import math

from dspin_constants import *

from gpiozero import LED, Button

bus = 0
cs_pin = 0

slave_select_pin = 25
reset_pin = 3
busy_pin = 2

slave_select_gpio = LED(slave_select_pin)
busy_gpio = Button(busy_pin)
reset_gpio = LED(reset_pin)
spi = spidev.SpiDev()


def dspin_xfer(data):
	data = data & 0xFF
	slave_select_gpio.off()

	result = spi.xfer([data])
	
	#spi.writebytes([data])
	#result = spi.readbytes(1)

	#print('xfering ' + hex(data))
	slave_select_gpio.on()
	return result[0]

def dspin_GetParam(param):
	dspin_xfer(dSPIN_GET_PARAM | param)
	return dspin_ParamHandler(param, 0)

def dspin_SetParam(param, value):
	dspin_xfer(dSPIN_SET_PARAM | param)
	dspin_ParamHandler(param, value)

def dspin_ParamHandler(param, value):
	if param == dSPIN_CONFIG:
		return dspin_param(value, 16)	
	elif param == dSPIN_STATUS:
		return dspin_param(0, 16)
	elif param == dSPIN_STEP_MODE:
		return dspin_xfer(value)
	elif param in [dSPIN_KVAL_RUN, dSPIN_KVAL_ACC, dSPIN_KVAL_DEC]:
		return dspin_xfer(value)
	elif param == dSPIN_ACC:
		return dspin_param(value, 12)
	elif param == dSPIN_MAX_SPEED:
		return dspin_param(value, 10)
	elif param == dSPIN_MIN_SPEED:
		return dspin_param(value, 12)
	elif param == dSPIN_FS_SPD:
		return dspin_param(value, 10)
	elif param == dSPIN_OCD_TH:
		return dspin_xfer(value & 0x0F)

	else:
		raise Exception('not implemented: ' + str(param))

def dspin_param(value, bit_length):
	byte_len = int(math.ceil(bit_length / 8.))
	
	mask = 0xffffffff >> (32 - bit_length)
	if value > mask: value = mask
	
	result = 0

	if byte_len == 3:
		result = result | (dspin_xfer(value>>16) << 16)
	if byte_len >= 2:
		result = result | (dspin_xfer(value>>8) << 8)
	if byte_len >= 1:
		result = result | (dspin_xfer(value))
	
	return result & mask
		
def dspin_GetStatus():
	temp = 0
	dspin_xfer(dSPIN_GET_STATUS)
	temp = dspin_xfer(0) << 8
	temp |= dspin_xfer(0)
	return temp

def dspin_Run(dir, speed):
	speed = int(speed)
	dspin_xfer(dSPIN_RUN | dir)
	if speed > 0xFFFFF: speed = 0xFFFFF

	dspin_xfer(speed >> 16)
	dspin_xfer(speed >> 8)
	dspin_xfer(speed)
		
def dspin_SoftStop():
	dspin_xfer(dSPIN_SOFT_STOP)

def dspin_SpdCalc(stepsPerSec):
	result = stepsPerSec * 67.106
	if result > 0x3FFF:
		result = 0x3FFF
	print('speed result: ', int(result))
	return int(result)

def connect_l6470():
	slave_select_gpio.on()
	reset_gpio.on()

	reset_gpio.on()
	time.sleep(0.1)
	reset_gpio.off()
	time.sleep(0.1)
	reset_gpio.on()
	time.sleep(0.1)
	
	spi.open(bus, cs_pin)
	spi.max_speed_hz = 10000
	spi.mode = 3
	spi.lsbfirst = False
	#spi.no_cs = True
	#spi.loop = False
	
	config_result = dspin_GetParam(dSPIN_CONFIG)
	print('config result: ', hex(config_result))
	
	config_result = dspin_GetParam(dSPIN_CONFIG)
	print('config result: ', hex(config_result))
	
	status = dspin_GetStatus()
	print('status: ', hex(status))
	
	dspin_SetParam(dSPIN_STEP_MODE, 
			(0xFF - dSPIN_SYNC_EN) | dSPIN_STEP_SEL_1_128 | dSPIN_SYNC_SEL_64)
	
	status = dspin_GetStatus()
	print('status: ', hex(status))
	
	dspin_SetParam(dSPIN_MIN_SPEED, 1)
	print('min speed: ', dspin_GetParam(dSPIN_MIN_SPEED))
	print('max speed: ', dspin_GetParam(dSPIN_MAX_SPEED))
	#max speed?
	
	dspin_SetParam(dSPIN_FS_SPD, 0x3FF)
	
	dspin_SetParam(dSPIN_ACC, 0xFF)
	
	dspin_SetParam(dSPIN_OCD_TH, dSPIN_OCD_TH_6000mA)
	
	dspin_SetParam(dSPIN_CONFIG,
			dSPIN_CONFIG_PWM_DIV_1 |
			dSPIN_CONFIG_PWM_MUL_2 |
			dSPIN_CONFIG_SR_180V_us |
			dSPIN_CONFIG_OC_SD_DISABLE |
			dSPIN_CONFIG_VS_COMP_DISABLE |
			dSPIN_CONFIG_SW_HARD_STOP |
			dSPIN_CONFIG_INT_16MHZ)
	
	dspin_SetParam(dSPIN_KVAL_RUN, 0x7F);
	dspin_SetParam(dSPIN_KVAL_ACC, 0x0F);
	dspin_SetParam(dSPIN_KVAL_DEC, 0x0F);
	
	status = dspin_GetStatus()
	print('status: ', hex(status))

def disconnect_l6470():
	dspin_SoftStop()
	spi.close()



if __name__ == "__main__":
	
	connect_l6470()
		
	seconds_per_rotation = (24.*60.*60.)
	gear_ratio = 128.
	steps_per_rotation = 400.
	steps_per_second = steps_per_rotation * gear_ratio / seconds_per_rotation 
	print('steps per second: ', steps_per_second)
	
	dspin_Run(FWD, dspin_SpdCalc(100*steps_per_second))
	time.sleep(10)
	
	disconnect_l6470()

