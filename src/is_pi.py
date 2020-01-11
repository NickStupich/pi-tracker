import os

# is_pi = True

if not 'uname' in dir(os): 
	is_pi = False
else:
	is_pi = 'raspberrypi' in os.uname()
