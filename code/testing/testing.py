import pyvisa, time, serial
from dac import *
from gpib import *
import spani_globals, scan

def test_dac(com_port, num_iterations, code_vec, dac_name, vfsr=3.3, precision=16, t_wait=.001):
	'''
	Inputs:
		com_port: String. Name of the COM port to connect to.
		num_iterations: Integer. Number of times to measure a single code.
		code_vec: Collection of integers. Codes to measure.
		num_bits: Collection of bits.
		dac_name: Indicates which DAC is being tested, e.g. OUT_DAC_MAIN,
			OUT_DAC_SMALL, OUT_VDD_MAIN, OUT_VDD_AON
		vfsr: Float. Voltage full scale range of the Teensy analogRead.
		precision: Integer. Number of bits used by Teensy in analogRead.
		t_wait: Float. Time in seconds to pause between each measurement
			from the voltmeter.
	Returns:
		code_data_dict: Mapping with key:value of digital code:collection of 
			analog measurements taken for that code. For example
			{0: [0, 1e-3],
			 1: [1, 1.1, 2, 0]}
	Raises:
		AssertionError: If a code in the collection of codes exceeds the
			number of bits permitted.
	Notes:
		TODO GPIB for digital multimeter is broken, hence the commented-out
		bits. Instead, it uses Teensy's analogRead.
	'''
	code_data_dict = {code:[] for code in code_vec}

	num_bits = spani_globals.N_BITS_MAP[dac_name]

	code_max = 1 << num_bits
	assert max(code_vec) < code_max, f'Code {max(code_vec)} exceeds allowable' \
		+ f'max {code_max}'

	# Connect to voltmeter
	# rm = pyvisa.ResourceManager()
	# vm = rsrc_open(rm)

	# Configure voltmeter
	# smu_raw = ''
	# while smu_raw.lower() not in ('a', 'b'):
	# 	smu_raw = input('Choose channel (a/b): ')
	# 	smu_raw = smu_raw.lower()
	# smu_sel = gpib.SMU_A if smu_raw=='a' else gpib.SMU_B
	# smu_str = f'smu{smu_sel}'
	# voltmeter_Keithley2634B_config(sm=vm, smu=smu_sel, autorange=True)

	# Open Teensy serial connection
	teensy_ser = serial.Serial(port=com_port,
                        baudrate=19200,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS,
                        timeout=1)

	# Take measurements, one step at a time
	for code in code_vec:
		# Convert code to binary for scan programming
		code_binary = [int(i) for i in list('{0:0b}'.format(code))] # MSB->LSB
		extra_zeros = [0]*(num_bits-len(code_binary)) # Zero padding as needed
		code_binary = extra_zeros + code_binary

		# Program scan 
		en_main = 1 if dac_name in (spani_globals.OUT_DAC_MAIN, 
			spani_globals.OUT_VDD_MAIN, 
			spani_globals.OUT_REF_PREAMP) \
			else 0 
		en_small = 1 if dac_name in (spani_globals.OUT_DAC_SMALL, 
			spani_globals.OUT_VDD_SMALL) else 0
		
		scan_arg_map = {
			spani_globals.OUT_DAC_MAIN 		: 'dac_sel',
			spani_globals.OUT_DAC_SMALL 	: 'dac_sel',
			spani_globals.OUT_REF_PREAMP	: 'vref_preamp',
			spani_globals.OUT_VDD_MAIN 		: 'vdd_signal',
			spani_globals.OUT_VDD_SMALL 	: 'vdd_signal',
			spani_globals.OUT_VDD_AON 		: 'vdd_aon'}

		teensy_arg_map = {
			spani_globals.OUT_DAC_MAIN		: b'dacreadmain\n',
			spani_globals.OUT_DAC_SMALL		: b'dacreadsmall\n',
			spani_globals.OUT_REF_PREAMP	: b'dacreadpreamp\n',
			spani_globals.OUT_VDD_MAIN		: b'dacreadvddmain\n',
			spani_globals.OUT_VDD_SMALL		: b'dacreadvddsmall\n',
			spani_globals.OUT_VDD_AON		: b'dacreadvddaon\n'}

		construct_scan_params = {
			scan_arg_map[dac_name]: code_binary,
			'en_main' : [en_main],
			'en_small': [en_small]}
		
		scan_bits = scan.construct_ASC(**construct_scan_params)

		# Take N=num_iterations measurements TODO
		for _ in range(num_iterations):
			# vm.write(f'print({smu_str}.measure.v())')
			try:
				cout = int(teensy_ser.readline())
				vout = vfsr * cout / (2**precision)
				# vout_str = vm.read()
				# vout = float(vout_str)
			except Exception as e:
				print(e)
				vout = float('nan')
			code_data_dict[code].append(vout)
			time.sleep(t_wait)

	# Close connection
	# vm.close()
	teensy_ser.close()
	return code_data_dict


def test_main(num_iterations, scan_dict, teensy_port,):
	'''
	Prompts the main signal chain with the same input periodically repeated.
	Inputs:
		num_iterations: Integer. Number of measurements to take.
		scan_dict: Dictionary to program the scan chain, with key:value
			of (argument):value. For example,
			{'preamp_res' : [1, 0],
			 'en_main' : [1]}
		teensy_port: String. Name of the COM port associated with Teensy.
	Returns:
		delay_vec: Collection of delays (in seconds) from the initial
			input trigger pulse and rising edge of the output pulse.
	'''
	# Program scan
	asc = construct_scan(**scan_dict)
	program_scan(com_port=teensy_port, ASC=asc)

	# Connect to function generator
	rm = pyvisa.ResourceManager()
	arb = rsrc_open(rm)

	# TODO Configure the function generator

	# TODO Turn on the output of the function generator

	# Turn off outputs and disconnect from function generator
	arb_close(arb)