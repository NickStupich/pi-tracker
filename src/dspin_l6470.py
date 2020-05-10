import time
import math
import threading
import datetime
from dspin_constants import *

import is_pi

if is_pi.is_pi:
	from gpiozero import LED
	from spidev import SpiDev
else:
    class LED(object):
        def __init__(*args): pass
        def on(self): pass
        def off(self): pass

    class SpiDev(object):
    	def __init__(*args):pass
    	def open(self, bus, cs_pin):pass
    	def xfer(self, data): return [0]
    	def close(self):pass

def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val 

class Dspin_motor(object):
	
	__has_toggled_reset_pin = False
	__spi_lock = None
	@classmethod
	def init_toggle_reset_pin(cls, reset_pin):
		if not cls.__has_toggled_reset_pin:
			cls.__has_toggled_reset_pin = True
			cls.reset_gpio = LED(reset_pin)
			cls.reset_gpio.on()
			time.sleep(0.1)
			cls.reset_gpio.off()
			time.sleep(0.1)
			cls.reset_gpio.on()
			time.sleep(0.1)
			Dspin_motor.__spi_lock = threading.Lock()


	def __init__(self, bus, cs_pin, slave_select_pin, reset_pin):
                Dspin_motor.init_toggle_reset_pin(reset_pin)

                self.slave_select_gpio = LED(slave_select_pin)
                self.spi = SpiDev()

                self.slave_select_gpio.on()

                self.spi.open(bus, cs_pin)
                self.spi.max_speed_hz = 10000
                self.spi.mode = 0
                self.spi.lsbfirst = False
                #spi.no_cs = True
                #spi.loop = False

                self.connect_l6470()
                self.last_steps_count_time = datetime.datetime.now()
                self.current_speed = 0
                self.absolute_pos_manual_count = 0

	def dspin_xfer(self, data):
		data = data & 0xFF
		self.slave_select_gpio.off()

		result = self.spi.xfer([data])
		
		#spi.writebytes([data])
		#result = spi.readbytes(1)

		#print('xfering ' + hex(data))
		self.slave_select_gpio.on()
		return result[0]

	def dspin_GetParam(self, param):
		self.dspin_xfer(dSPIN_GET_PARAM | param)
		return self.dspin_ParamHandler(param, 0)

	def dspin_SetParam(self, param, value):
		self.dspin_xfer(dSPIN_SET_PARAM | param)
		self.dspin_ParamHandler(param, value)

	def dspin_ParamHandler(self, param, value):
		if param == dSPIN_CONFIG:
			return self.dspin_param(value, 16)	
		elif param == dSPIN_STATUS:
			return self.dspin_param(0, 16)
		elif param == dSPIN_STEP_MODE:
			return self.dspin_xfer(value)
		elif param in [dSPIN_KVAL_RUN, dSPIN_KVAL_ACC, dSPIN_KVAL_DEC]:
			return self.dspin_xfer(value)
		elif param == dSPIN_ACC:
			return self.dspin_param(value, 12)
		elif param == dSPIN_MAX_SPEED:
			return self.dspin_param(value, 10)
		elif param == dSPIN_MIN_SPEED:
			return self.dspin_param(value, 12)
		elif param == dSPIN_FS_SPD:
			return self.dspin_param(value, 10)
		elif param == dSPIN_OCD_TH:
			return self.dspin_xfer(value & 0x0F)
		elif param == dSPIN_ABS_POS:
			return self.dspin_param(value, 22)

		else:
			raise Exception('not implemented: ' + str(param))

	def dspin_param(self, value, bit_length):
		byte_len = int(math.ceil(bit_length / 8.))
		
		mask = 0xffffffff >> (32 - bit_length)
		if value > mask: value = mask
		
		result = 0

		if byte_len == 3:
			result = result | (self.dspin_xfer(value>>16) << 16)
		if byte_len >= 2:
			result = result | (self.dspin_xfer(value>>8) << 8)
		if byte_len >= 1:
			result = result | (self.dspin_xfer(value))
		
		return result & mask
			
	def dspin_GetStatus(self):
		Dspin_motor.__spi_lock.acquire()
		temp = 0
		self.dspin_xfer(dSPIN_GET_STATUS)
		temp = self.dspin_xfer(0) << 8
		temp |= self.dspin_xfer(0)
		Dspin_motor.__spi_lock.release()
		return temp

	def dspin_Run(self, dir, speed):
                speed = int(speed)
                # print('speed: ', speed)
                Dspin_motor.__spi_lock.acquire()
                self.dspin_xfer(dSPIN_RUN | dir)
                if speed > 0xFFFFF: speed = 0xFFFFF

                self.dspin_xfer(speed >> 16)
                self.dspin_xfer(speed >> 8)
                self.dspin_xfer(speed)
                Dspin_motor.__spi_lock.release()
                
                self.current_speed = speed * (1 if dir == FWD else -1)

	def dspin_SoftStop(self):
		Dspin_motor.__spi_lock.acquire()
		self.dspin_xfer(dSPIN_SOFT_STOP)
		Dspin_motor.__spi_lock.release()

	def dspin_SpdCalc(self, stepsPerSec):
		result = stepsPerSec * 67.106
		#if result > 0x3FFF:
		#	result = 0x3FFF
		# print('speed result: ', int(result))
		return int(result)

	def dspin_GetPositionSteps(self):
                
                Dspin_motor.__spi_lock.acquire()
                result = self.dspin_GetParam(dSPIN_ABS_POS)
                result = twos_comp(result, 22)
                Dspin_motor.__spi_lock.release()
                
                #result &= 0xFF80
                result /= 16
                
                now = datetime.datetime.now()
                elapsed_seconds = (now - self.last_steps_count_time).total_seconds()
                self.last_steps_count_time = now
                
                steps_change = elapsed_seconds * self.current_speed/67.106
                self.absolute_pos_manual_count += steps_change
                #print(result, self.absolute_pos_manual_count)
                return self.absolute_pos_manual_count

                return result

	def connect_l6470(self):
		
		config_result = self.dspin_GetParam(dSPIN_CONFIG)
		print('config result: ', hex(config_result))
		
		config_result = self.dspin_GetParam(dSPIN_CONFIG)
		print('config result: ', hex(config_result))
		
		status = self.dspin_GetStatus()
		print('status: ', hex(status))
		
		self.dspin_SetParam(dSPIN_STEP_MODE, 
                           (0xFF - dSPIN_SYNC_EN) | dSPIN_STEP_SEL_1_128 | dSPIN_SYNC_SEL_64)
		
		status = self.dspin_GetStatus()
		print('status: ', hex(status))
		
		self.dspin_SetParam(dSPIN_MIN_SPEED, 1)
		#self.dspin_SetParam(dSPIN_MAX_SPEED, 2000)
		print('min speed: ', self.dspin_GetParam(dSPIN_MIN_SPEED))
		print('max speed: ', self.dspin_GetParam(dSPIN_MAX_SPEED))
		#max speed?
		
		self.dspin_SetParam(dSPIN_FS_SPD, 0x3FF)
		
		self.dspin_SetParam(dSPIN_ACC, 0xFF)
		
		self.dspin_SetParam(dSPIN_OCD_TH, dSPIN_OCD_TH_6000mA)
		
		self.dspin_SetParam(dSPIN_CONFIG,
				dSPIN_CONFIG_PWM_DIV_1 |
				dSPIN_CONFIG_PWM_MUL_2 |
				dSPIN_CONFIG_SR_180V_us |
				dSPIN_CONFIG_OC_SD_DISABLE |
				dSPIN_CONFIG_VS_COMP_DISABLE |
				dSPIN_CONFIG_SW_HARD_STOP |
				dSPIN_CONFIG_INT_16MHZ)
		
		self.dspin_SetParam(dSPIN_KVAL_RUN, 0x7F);
		self.dspin_SetParam(dSPIN_KVAL_ACC, 0x0F);
		self.dspin_SetParam(dSPIN_KVAL_DEC, 0x0F);
		
		status = self.dspin_GetStatus()
		print('status: ', hex(status))

	def disconnect_l6470(self):
		self.dspin_SoftStop()
		self.spi.close()



if __name__ == "__main__":
		

	#bus = 1
	bus=1
	cs_pin = 0

	slave_select_pin = 25
	#slave_select_pin=12
	# busy_pin = 2
	reset_pin = 3

	motor1 = Dspin_motor(bus, cs_pin, 25, reset_pin)
	motor2 = Dspin_motor(bus, cs_pin, 26, reset_pin)
	speed = 2000
	motor1.dspin_Run(FWD, motor1.dspin_SpdCalc(speed))
	time.sleep(2); print(motor1.dspin_GetPositionSteps()); motor1.dspin_Run(REV, motor1.dspin_SpdCalc(speed))
	time.sleep(2)
	motor1.dspin_SoftStop()
	motor2.dspin_Run(FWD, motor2.dspin_SpdCalc(speed))
	time.sleep(2)
	motor2.dspin_Run(REV, motor2.dspin_SpdCalc(speed))

	time.sleep(2)

	motor1.disconnect_l6470()
	motor2.disconnect_l6470()
