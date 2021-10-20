import serial
import random
import os
import sys
import time
import struct
import difflib

from typing import List, Mapping

def program_scan(com_port, ASC) -> None:
	'''
	Inputs:
		com_port: String. Name of the COM port to connect to.
		ASC: List of integers. Analog scan chain bits.
	Returns:
		None.
	Raises:
		ValueError if scan in doesn't match scan out.
	'''
	# Open COM port to Teensy to bit-bang scan chain
	ser = serial.Serial(port=com_port,
		baudrate=19200,
		parity=serial.PARITY_NONE,
		stopbits=serial.STOPBITS_ONE,
		bytesize=serial.EIGHTBITS)

	# Convert array to string for UART
	ASC_string = ''.join(map(str,ASC))

	# Send string to Teensy to program into the chip
	ser.write(b'ascwrite\n')
	print(ser.readline())


	# Execute oad command to latch values inside chip
	ser.write(b'ascload\n')
	print(ser.readline())

	# Read back scan chain contents
	ser.write(b'ascread\n')
	x = ser.readline()
	scan_out = x[::-1]

	print(ASC_string)
	print(scan_out.decode())

	# Compare what was written to what was read back
	ser.close()
	if int(ASC_string) == int(scan_out.decode()):
		print('Read matches write')
	else:
		raise ValueError('Read/write comparison incorrect')

def construct_ASC(preamp_res 	=[0]*2,
				delay_res 		=[0]*2,
				watchdog_res	=[0],
				attenuator_sel 	=[0]*3,
				dac_sel 		=[0]*8,
				az_main_gain 	=[0]*3,
				az_aux_gain 	=[0]*3,
				oneshot_res 	=[0]*2,
				vref_preamp 	=[0]*8,
				vdd_aon 		=[0]*5,
				vdd_signal 		=[0]*5,
				en_main 		=[0],
				en_small		=[0]) -> List[int]:
	'''
	Inputs:
	Returns:
		asc: List of 0 and 1. MSB -> LSB, i.e. bit0 of the scan chain
			goes at idx0.
	Notes:
		All inputs are MSB -> LSB, i.e. arg[0] corresponds to its MSB.
	'''
	# TODO check for reversing the list

	# Reverse everything to be LSB -> MSB
	preamp_res_rev 		= preamp_res[::-1]
	delay_res_rev		= delay_res[::-1]
	attenuator_sel_rev 	= attenuator_sel[::-1]
	dac_sel_rev 		= dac_sel[::-1]
	az_main_gain_rev	= az_main_gain[:-1]
	az_aux_gain_rev 	= az_aux_gain[::-1]
	oneshot_res_rev		= oneshot_res[::-1]
	vref_preamp_rev		= vref_preamp[::-1]
	vdd_aon_rev			= vdd_aon[::-1]
	vdd_signal_rev		= vdd_signal[::-1]

	# Initialize with invalid values to make sure no bit is missed
	asc = [2] * 44

	# preamp_res
	for i, idx in enumerate((8, 13)):
		asc[idx] = preamp_res_rev[i]

	# delay_res
	for i, idx in enumerate((10, 11)):
		asc[idx] = delay_res_rev[i]

	# watchdog_res
	asc[30] = watchdog_res[0]

	# attenuator_sel
	for i, idx in enumerate((9, 12, 31)):
		asc[idx] = attenuator_sel_rev[i]

	# dac_sel
	for i, idx in enumerate((2, 3, 18, 25, 4, 17, 26, 5)):
		asc[idx] = dac_sel_rev[i]

	# az_main_gain
	for i, idx in enumerate((1, 20, 23)):
		asc[idx] = az_main_gain_rev[i]

	# az_aux_gain
	for i, idx in enumerate((0, 21, 22)):
		asc[idx] = az_aux_gain_rev[i]

	# oneshot_res
	for i, idx in enumerate((19, 24)):
		asc[idx] = oneshot_res_rev[i]

	# vref_preamp
	for i, idx in enumerate((16, 27, 6, 15, 28, 7, 14, 29)):
		asc[idx] = vref_preamp_rev[i]

	# vdd_aon + vdd_signal
	asc[34:39] = vdd_aon_rev
	asc[39:44] = vdd_signal_rev

	# en_main + small
	asc[32] = en_main[0]
	asc[33] = en_small[0]

	return asc