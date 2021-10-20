import pyvisa
import serial

Z_INF = 'INF'
Z_FIFTY = '50OHM'

def rsrc_open(rm):
	'''
	Inputs:
		rm: PyVISA Resource manager.
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
		print(rsrc.query("*IDN?"))
		is_correct_raw = input('Is this the correct device? (y/n): ').lower()
		is_correct = (is_correct_raw == 'y')

		# If not correct, close the connection and prompt again
		if not is_correct:
			rsrc.close()

	return rsrc

def psu_close(psu):
	'''
	Turns off outputs and closes connection with DC power supply.
	Inputs:
		psu: Visa Resource object. The device with an opened connection to be
			closed.
	Returns:
		None.
	'''
	# TODO turn off outputs
	psu.close()


def multimeter_close(multimeter):
	'''
	Closes connection to digital multimeter.
	Inputs:
		multimeter: Visa Resource object. The device with an opened connection
			to be closed.
	Returns:
		None.
	'''
	multimeter.close()


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