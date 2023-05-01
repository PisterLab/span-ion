import serial
import random
import os
import sys
import time
import struct
import difflib

from typing import List, Mapping

def program_scan(ser, ASC) -> None:
	'''
	Inputs:
		ser: serial.Serial. Open COM port to the microcontroller.
		ASC: List of integers. Analog scan chain bits.
	Returns:
		None.
	Raises:
		ValueError if scan in doesn't match scan out.
	Notes:
		Closes serial connection if scan in doesn't match scan out.
	'''
	# Convert array to string for UART
	ASC_string = ''.join(map(str,ASC))

	# Send string to Teensy to program into the chip
	print("Writing...")
	ser.write(b'ascwrite\n')
	print(ser.readline())
	ser.write(ASC_string.encode())
	print(ser.readline())

	# Execute load command to latch values inside chip
	print("Loading...")
	ser.write(b'ascload\n')
	print(ser.readline())

	# Read back scan chain contents
	print("Reading...")
	ser.write(b'ascread\n')
	x = ser.readline()
	scan_out = x[::-1]

	print(ASC_string)
	print(scan_out.decode()[::-1])

	if int(ASC_string) == int(scan_out.decode()[::-1]):
		print('Read matches write')
	else:
		raise ValueError(f'Read/write comparison incorrect {ASC_string}|{int(scan_out.decode())}')
		teensy_ser.close()


def construct_ASC(preamp_res 		=[0]*2,
				delay_res 			=[0]*2,
				watchdog_res		=[0],
				en_stuck 			=[0],
				attenuator_sel 		=[0]*3,
				dac_sel 			=[0]*8,
				oneshot_res 		=[0]*2,
				vref_preamp 		=[0]*8,
				en_pullup_p_led 	=[0]*7,
				en_pullup_n_led 	=[0]*7,
				en_pullup_p_cfd 	=[0]*7,
				en_pullup_n_cfd 	=[0]*7,
				en_pulldown_p_led 	=[0]*7,
				en_pulldown_n_led 	=[0]*7,
				en_pulldown_p_cfd 	=[0]*7,
				en_pulldown_n_cfd	=[0]*7,
				ctrl_pullup_led 	=[0]*28,
				ctrl_pulldown_led 	=[0]*28,
				ctrl_pullup_cfd		=[0]*28,
				ctrl_pulldown_cfd 	=[0]*28,
				vdd_aon 			=[0]*5,
				vdd_signal 			=[0]*5,
				en_main 			=[0],
				en_small			=[0]) -> List[int]:
	'''
	Inputs:
		arg: List of 0 and 1. MSB -> LSB.
	Returns:
		asc: List of 0 and 1. MSB -> LSB, i.e. bit0 of the scan chain
			goes at idx[n-1].
	Notes:
		All inputs are MSB -> LSB, i.e. arg[0] corresponds to its MSB.
	'''
	# TODO check for reversing the list

	# Reverse everything to be LSB -> MSB
	preamp_res_rev 			= preamp_res[::-1]
	delay_res_rev			= delay_res[::-1]
	attenuator_sel_rev 		= attenuator_sel[::-1]
	dac_sel_rev 			= dac_sel[::-1]
	oneshot_res_rev			= oneshot_res[::-1]
	vref_preamp_rev			= vref_preamp[::-1]
	en_pullup_p_led_rev 	= en_pullup_p_led[::-1]
	en_pullup_n_led_rev 	= en_pullup_n_led[::-1]
	en_pullup_p_cfd_rev 	= en_pullup_p_cfd[::-1]
	en_pullup_n_cfd_rev 	= en_pullup_n_cfd[::-1]
	en_pulldown_p_led_rev 	= en_pulldown_p_led[::-1]
	en_pulldown_n_led_rev 	= en_pulldown_n_led[::-1]
	en_pulldown_p_cfd_rev 	= en_pulldown_p_cfd[::-1]
	en_pulldown_n_cfd_rev 	= en_pulldown_n_cfd[::-1]
	ctrl_pullup_led_rev 	= ctrl_pullup_led[::-1]
	ctrl_pulldown_led_rev 	= ctrl_pulldown_led[::-1]
	ctrl_pullup_cfd_rev		= ctrl_pullup_cfd[::-1]
	ctrl_pulldown_cfd_rev 	= ctrl_pulldown_cfd[::-1]
	vdd_aon_rev				= vdd_aon[::-1]
	vdd_signal_rev			= vdd_signal[::-1]

	# Initialize with invalid values to make sure no bit is missed
	asc = [2] * 207

	asc_map = {preamp_res_rev 		: (101, 102),
			delay_res_rev 			: (48, 71),
			watchdog_res 			: tuple([144]),
			en_stuck 				: tuple([120]),
			attenuator_sel_rev 		: (143, 59, 60),
			dac_sel_rev 			: (58, 61, 100, 103, 142, 145, 184, 187),
			oneshot_res_rev 		: (186, 185),
			vref_preamp_rev 		: (57, 62, 99, 104, 141, 146, 183, 188),
			en_pullup_p_led_rev 	: (182, 56, 97, 138, 179, 53, 94),
			en_pullup_n_led_rev 	: (189, 623, 106, 149, 192, 66, 109),
			en_pullup_p_cfd_rev		: (4, 7, 16, 20, 28, 36, 74),
			en_pullup_n_cfd_rev 	: (5, 6, 17, 19, 29, 35, 87),
			en_pulldown_p_led_rev 	: (135, 164, 92, 39, 124, 82, 155),
			en_pulldown_n_led_rev 	: (152, 165, 111, 80, 133, 121, 174),
			en_pulldown_p_cfd_rev 	: (117, 159, 46, 157, 84, 126, 41),
			en_pulldown_n_cfd_rev 	: (75, 158, 85, 127, 42, 89, 161),
			ctrl_pullup_led_rev		: (147, 140, 105, 98, 190, 181, 148, 139, 64, 55, 191, 180, 107, 96, 65, 54, 150, 137, 108, 95, 193, 178, 151, 136, 67, 52, 194, 177),
			ctrl_pulldown_led_rev	: (110, 93, 68, 51, 176, 153, 134, 123, 69, 50, 122, 81, 166, 163, 175, 154, 112, 91, 70, 49, 79, 40, 167, 162, 132, 125, 113, 90),
			ctrl_pullup_cfd_rev		: (0, 1, 2, 3, 11, 10, 9, 8, 12, 13, 14, 15, 24, 23, 22, 21, 18, 25, 26, 27, 30, 31, 38, 37, 34, 33, 32, 45),
			ctrl_pulldown_cfd_rev	: (128, 44, 116, 86, 43, 129, 170, 171, 88, 76, 73, 118, 160, 115, 172, 130, 47, 169, 119, 77, 156, 72, 131, 114, 83, 173, 78, 168),
			vdd_aon_rev				: (204, 196, 205, 195, 206),
			vdd_signal_rev			: (199, 202, 198, 203, 197),
			en_main					: tuple([201]),
			en_small				: tuple([200])}

	for bit_lst, idx_tup in asc_map.items():
		for i, idx in enumerate(idx_tup):
			asc[idx] = bit_lst[i]

	# TODO I think I need to invert one more time?
	asc = [int(-(b-1)) for b in asc]
	return asc