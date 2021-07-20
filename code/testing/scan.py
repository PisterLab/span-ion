import serial
import random
import os
import sys
import time
import struct
import difflib

def program_scan(com_port, ASC):
	'''
	Inputs:
		com_port: String. Name of the COM port to connec tto.
		ASC: List of integers. Analog scan chain bits.
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

	# Comparewhat was written to what was read back
	ser.close()
	if int(ASC_string) == int(scan_out.decode()):
		print('Read matches write')
	else:
		raise ValueError('Read/write comparison incorrect')

	return

def construct_ASC():
