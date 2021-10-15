import serial
import visa
import warnings
from gpib import arb_open, arb_config, arb_close

def read_tac(com_port, vdd, chain):
	'''
	Inputs:
		com_port: String. Name of the COM port to connect to.
		vdd: Float. Reference voltage for the ADC on the Teensy.
		chain: String "main" or "small" (not case sensitive) to
			read from the main or small signal chain, respectively.
	'''
	# Sanity check for which signal chain to prompt
	if chain.lower() not in ('main', 'small'):
		warnings.warn(f'Signal chain name should be main or small, not {chain}')

	# Open COM port to Teensy
	ser = serial.Serial(port=com_port,
		baudrate=19200,
		parity=serial.PARITY_NONE,
		stopbits=serial.STOPBITS_ONE,
		bytesize=serial.EIGHTBITS)

	# Prompt the Teensy to read from the ADC
	if chain.lower() == 'main':
		ser.write(b'tacmainread\n')
	elif chain.lower() == 'small':
		ser.write(b'tacsmallread\n')

	# Get the value from the Teensy
	adc_out_raw = ser.readline()
	adc_out_str = adc_out_raw.decode('utf-8').replace('\n', '')
	try:
		adc_out = int(adc_out_str)
	except ValueError:
		warnings.warn(f'{adc_out} not an integer')

	# 

def prompt_dac(src, output_num, vout):
	'''
	Sets a voltage supply to a known value for DAC override.
	Inputs:
		src_name: String. Name to use in the connection for the 
			DC voltage source.
		output_num: Integer; likely 1 or 2. The output source used for testing
			for waveform generators with multiple output sources.
		vout: Float. Intended output voltage.
	Notes:
		The input impedance of the chip at this pad is not strictly
		capacitive.
	'''
	arb.write(f'SOURCE{output_num}:VOLTAGE:OFFSET {vout}')

def read_dac(meas_name):
	'''
	Measures the voltage from the DAC via some voltmeter.
	Inputs:
		meas_name:
	Returns:
	'''
	pass


def prompt_noshape(arb_name, ):
	'''
	Opens a connection with the arbitrary waveform generator and
	prompts the no-shape chain with input voltages.
	Inputs:
		arb_name: String. Name to use in the connection for the waveform 
			generator, e.g. "USB0::0x0957::0x2C07::MY57801384::0::INSTR"
	'''
	# Interface with waveform generators
	arb = arb_open(arb_name)
	rm = visa.ResourceManager()
	arb = rm.open_resource(arb_name)
	
	# Sanity checking that it's the correct device
	arb.query("*IDN?")

	# Zin setting expected by arbs is capacitive
	arb.write("OUTPUT1:LOAD INF")
	arb.write("SOURCE1:FUNCTION DC") # TODO change
	arb.write("OUTPUT2:LOAD INF")
	arb.write("SOURCE2:FUNCTION DC") # TODO change

	# Setting the waveform generator to 0 initially to avoid breaking things
	arb.write("SOURCE1:VOLTAGE:OFFSET 0") # TODO remove
	arb.write("SOURCE2:VOLTAGE:OFFSET 0")

	# TODO: generate waveforms with as-of-yet unknown parameters
	pass


def prompt_main(teensy_ser, arb_name, output_num):
	'''
	Opens a connection with the arbitrary waveform generator and 
	prompts the full chain with the appropriate input voltages.
	Inputs:
		arb_name: String. Name to use in the connection for the waveform 
			generator, e.g. "USB0::0x0957::0x2C07::MY57801384::0::INSTR"
	'''
	# Interface with waveform generator
	arb = arb_open(arb_name)
	arb_config(arb, output_num, "50OHM")

	# Reset the TAC
	teensy_ser.write(b'tacreset\n')

	# TODO prompt the signal chain
	pass

	# Disconnect from the arb
	arb_close(arb)