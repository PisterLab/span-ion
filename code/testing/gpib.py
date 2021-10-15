import visa
import serial

Z_INF = 'INF'
Z_FIFTY = '50OHM'

def arb_open(arb_name):
	'''
	Inputs:
		arb_name: String. Name to use in the connection for the waveform 
			generator, e.g. "USB0::0x0957::0x2C07::MY57801384::0::INSTR"
		output_num: Integer; likely 1 or 2. The output source used for testing
			for waveform generators with multiple output sources.
	Returns:
		arb: Visa Resource object. The device to be opened.
		rm: Visa ResourceManager object. The resource manager with which to 
			open interfaces with various GPIB elements.
	'''
	# Interface with voltage supply
	rm = visa.ResourceManager()
	arb = rm.open_resource(meas_name)

	# Sanity checking that it's the correct device
	arb.query("*IDN?")

	return arb, rm

def arb_config(arb, output_num, zin):
	'''
	Inputs:
		arb:
		output_num:
		zin: 
	Returns:
		
	'''
	arb.write(f"OUTPUT{output_num}:LOAD {zin}")


def arb_close(arb):
	'''
	Turns off outputs and closes connection with arbitrary waveform generator.
	Inputs:
		arb: Visa Resource object. The device with an opened connection
			to be closed.
	'''
	arb.write("OUTPUT1 OFF")
	arb.write("OUTPUT2 OFF")

	arb.close()