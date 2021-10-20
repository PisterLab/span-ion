import serial
import random
import os
import sys
import time
import struct
import difflib

from scan import program_scan, construct_scan
from 

if __name__ == "__main__":
	teensy_port = 'COM22'

	####################
	### Program Scan ###
	####################
	if False:
		asc_params = dict(
			# MSB -> LSB
			preamp_res 		= [0, 0],
			delay_res 		= [0, 0],
			watchdog_res 	= [0, 0, 0, 0],
			attenuator_sel	= [0, 0, 0],
			dac_sel 		= [0, 0, 0, 0, 0, 0, 0, 0],
			az_main_gain 	= [0, 0, 0],
			az_aux_gain 	= [0, 0, 0],
			oneshot_res 	= [0, 0],
			vref_preamp 	= [0, 0, 0, 0, 0, 0, 0, 0],
			vdd_aon			= [0, 0, 0, 0, 0],
			vdd_signal		= [0, 0, 0, 0, 0],
			en_main			= [0],
			en_small		= [0])

		asc = construct_scan(**asc_params)
		program_scan(com_port=teensy_port, ASC=asc)

	#####################
	### Test LED DACs ###
	#####################
	if False:
		test_dac_params = dict(
			iterations=100,
			code_vec=range()
			)