import pyvisa
import serial

Z_INF = 'INF'
Z_FIFTY = '50OHM'

def rsrc_open(rm, rsrc_name):
	'''
	Inputs:
		rm: PyVISA Resource manager.
		rsrc_name: String. Name to use in the connection for the hardware, 
			e.g. "USB0::0x0957::0x2C07::MY57801384::0::INSTR" or 
			"GPIB0::5::INSTR"
	Returns:
		rsrc: Visa Resource object. The device to be opened.
	'''
	is_correct = False
	while not is_correct:
		# List resources for user selection by index
		print('Index: Resource ID')
		for i, x in enumerate(rm.list_resources()):
			print(f'{i}: {x}')
		idx_str = input('Choose Device Index: ')
		rsrc = rm.open_resource(rm.list_resources[int(idx)])

		# Sanity checking that it's the correct device
		rsrc.query("*IDN?")
		is_correct_raw = input('Is this the correct device? (y/n): ').lower()
		is_correct = (is_correct_raw == 'y')

		# If not correct, close the connection and prompt again
		if not is_correct:
			rsrc.close()

	return rsrc

def arb_config(arb, output_num, zin):
	'''
	Inputs:
		arb: Visa Resource object. The opened device.
		output_num: Integer. Index of the output source, i.e. 1 or 2 in our case.
		zin: String gpib.Z_INF or gpib.Z_FIFTY (see above). Not sure what
			this will do if it attempts to set to something invalid, but
			it probably won't be pretty.
	Returns:
		None.
	'''
	arb.write(f"OUTPUT{output_num}:LOAD {zin}")
	return

def arb_close(arb):
	'''
	Turns off outputs and closes connection with arbitrary waveform generator.
	Inputs:
		arb: Visa Resource object. The device with an opened connection
			to be closed.
	Returns:
		None.
	'''
	arb.write("OUTPUT1 OFF")
	arb.write("OUTPUT2 OFF")

	arb.close()
	return