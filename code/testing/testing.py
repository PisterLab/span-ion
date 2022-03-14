import pyvisa, serial, minimalmodbus
import time, sys, os
from dac import *
from gpib import *
import spani_globals, scan, temp_chamber, tdc
from pprint import pprint

def test_offset_small(teensy_port, aux_port, num_iterations, vtest_dict, vdd=1.8,
		vfsr=3.3, precision=16, tref_clk=1/15e6):
	'''
	Inputs:
		teensy_port:
		aux_port:
		num_iterations: Integer. Number of times to measure for a single
			voltage setup.
		vtest_dict: Dictionary. Key:value is (DC bias):(collection of 
			differential input voltages). e.g. {0.5 : [0.1, -0.1]} corresponds to
			(negative input, positive input) as (0.45,0.55)V and (0.55,0.45)V.
		vdd: Float. Supply voltage of the device in question. This will put a
			cap on the maximum input voltage.
		vfsr: Float. The Teensy analogWrite full scale range in volts.
		precision: Integer. The number of bits to use in _both_ Teensies'
			analogRead and analogWrite.
		tref_clk: Float. Clock period of the reference clock in seconds.
	Returns:
		overflow_fracs: Dictionary. Key:value is (input common mode):
			dict(vdiff_vec=collection of differential voltages, overflow_fracs=
			(collection of floats that are the # of times there was overflow/
			number of iterations for that single differential voltage))
	Notes:
		Intended for use in measuring the static offset of the ZCD.
		Highly recommend having at least 100 iterations to account for noise.
		The argument for precision should match whatever's in the Teensy code!
	'''
	overflow_fracs = {vincm:dict(vdiff_vec=tuple(), overflow_fracs=tuple())
		for vincm in vtest_dict.keys()}

	# Open serial connections
	teensy_ser = serial.Serial(port=teensy_port,
                    baudrate=19200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=5)

	aux_ser = serial.Serial(port=aux_port,
                    baudrate=19200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=5)

	# Discretization of the Teensy output voltage
	vlsb = vfsr / (2**precision)

	# Construct the TDC config commands
	wdata1_dict = dict(force_cal=1,
			parity_en=0,
			trigg_edge=0,
			stop_edge=0,
			start_edge=0,
			meas_mode=1,
			start_meas=1)
	wdata1 = tdc.construct_wdata1(**wdata1_dict)
	int_command1, int_wdata1 = tdc.construct_config(is_read=False, 
		addr=int(tdc.reg_addr_map['CONFIG1'], 16),
		wdata=wdata1)

	wdata2_dict = dict(calibration2_periods=1,
			avg_cycles=0,
			num_stop=0)
	wdata2 = tdc.construct_wdata2(**wdata2_dict)
	num_timers = tdc.code_numstop_map[wdata2_dict['num_stop']]
	int_command2, int_wdata2 = tdc.construct_config(is_read=False,
		addr=int(tdc.reg_addr_map['CONFIG2'], 16),
		wdata=wdata2)

	# Iterate through all input voltage input settings
	for vincm, vdiff_vec in vtest_dict.items():
		overflow_vec = []

		for vdiff in vdiff_vec:
			vinp, vinn = spani_globals.vdiff_conv(vincm, vdiff)
			codep = int(round(vinp / vlsb))
			coden = int(round(vinn / vlsb))

			count_overflow = 0
			for _ in range(num_iterations):
				# Reset the TDC
				print('Resetting TDC')
				aux_ser.write(b'zcdcomppsmall\n')
				aux_ser.write(int(0).to_bytes(2, 'big'))
				aux_ser.readline()
				aux_ser.write(b'zcdcompnsmall\n')
				aux_ser.write(int(round(vfsr / vlsb)-1).to_bytes(2, 'big'))
				aux_ser.readline()
				teensy_ser.write(b'tdcsmallreset\n')
				print(aux_ser.readline())
				
				# Configure the TDC
				print('--- Configuring CONFIG1')
				teensy_ser.write(b'tdcsmallconfig\n')
				teensy_ser.write(int_command1.to_bytes(1, 'big'))
				teensy_ser.write(int_wdata1.to_bytes(1, 'big'))
				for _ in range(5):
					print(teensy_ser.readline())

				print('--- Configuring CONFIG2')
				teensy_ser.write(b'tdcsmallconfig\n')
				teensy_ser.write(int_command2.to_bytes(1, 'big'))
				teensy_ser.write(int_wdata2.to_bytes(1, 'big'))
				for _ in range(5):
					print(teensy_ser.readline())

				# Set ZCD input voltages
				aux_ser.write(b'zcdcomppsmall\n')
				aux_ser.write(codep.to_bytes(2, 'big'))
				print(f'P: {aux_ser.readline()}')
				aux_ser.write(b'zcdcompnsmall\n')
				aux_ser.write(coden.to_bytes(2, 'big'))
				print(f'N: {aux_ser.readline()}')

				# Feed the start pulse
				teensy_ser.write(b'tdcsmallstart\n')
				print(aux_ser.readline())

				# Read data from interrupt status register
				has_finished = False
				while not has_finished:
					val_reg = 0
					int_cmd, _ = tdc.construct_config(is_read=True,
						addr=int(tdc.reg_addr_map['INT_STATUS'], 16))
					print(f'--- Reading INT_STATUS')
					teensy_ser.write(b'tdcsmallread\n')
					teensy_ser.write(int_cmd.to_bytes(1, 'big'))
					for _ in range(4):
						print(teensy_ser.readline())

					num_bytes = tdc.reg_size_map['INT_STATUS']//8
					for i in range(num_bytes):
						val_bytes = teensy_ser.readline().strip()
						val_int = int.from_bytes(val_bytes, byteorder='big',
							signed='False')
						val_reg = (val_reg << 8) + val_int

					print(f'-> {hex(val_reg)}')
				
					has_started = tdc.is_started(val_reg)
					has_finished = tdc.is_done(val_reg)
					has_ovfl_clk = tdc.is_overflow_clk(val_reg)
					has_ovfl_coarse = tdc.is_overflow_coarse(val_reg)

					# Sanity checking with some visibility
					print(f'\t Measurement Started: {has_started}')
					print(f'\t Measurement Done: {has_finished}')
					print(f'\t Clock Overflow: {has_ovfl_clk}')
					print(f'\t Coarse Overflow: {has_ovfl_coarse}')

				# Determine if there was overflow
				has_ovfl = has_ovfl_clk or has_ovfl_coarse
				
				# If there was, count it for that particular differential input
				if has_ovfl:
					count_overflow = count_overflow + 1
			overflow_vec.append(float(count_overflow/num_iterations))

		overflow_fracs[float(vincm)]['vdiff_vec'] = [float(vdiff) for vdiff in vdiff_vec]
		overflow_fracs[float(vincm)]['overflow_fracs'] = list(overflow_vec)

	return overflow_fracs

# def test_slow_zcd(teensy_port, aux_port, num_iterations, vtest_dict,
# 	vfsr=3.3, precision=16, tref_clk=1/16e6):
# 	'''
# 	Inputs:
# 		teensy_port: String. Name of the COM port the main board Teensy is 
# 			connected to.
# 		aux_port: String. Name of the COM port the auxiliary Teensy is connected
# 			to.
# 		num_iterations: Integer. Number of times to measure for a single 
# 			voltage setup.
# 		vtest_dict: Dictionary. Key:value is (DC bias):(collection of 
# 			differential input voltages). e.g. {0.5 : [0.1, -0.1]} corresponds to
# 			(negative input, positive input) as (0.45,0.55)V and (0.55,0.45)V.
# 		vfsr: Float. The Teensy analogWrite full scale range in volts.
# 		precision: Integer. The number of bits to use in _both_ Teensies'
# 			analogRead and analogWrite.
# 		tref_clk: Float. Clock period of the reference clock in seconds.
# 	Returns:
# 		high_rate_dict: Dictionary. Key:value is vincm:dict(vdiff_vec, rate_vec=(approximate
# 			1/time between stop events, capped out at 1/(TDC dynamic range)).
# 	Notes:
# 		Intended for use in measuring the static offset and input-referred noise
# 			of the ZCD.
# 		Highly recommend having a high number of iterations to account for 
# 			noise.
# 		The argument for precision should match whatever's in the Teensy code!
# 	'''
# 	high_rate_dict = dict()

# 	# Open serial connections
# 	teensy_ser = serial.Serial(port=teensy_port,
#                     baudrate=19200,
#                     parity=serial.PARITY_NONE,
#                     stopbits=serial.STOPBITS_ONE,
#                     bytesize=serial.EIGHTBITS,
#                     timeout=5)

# 	aux_ser = serial.Serial(port=aux_port,
#                     baudrate=19200,
#                     parity=serial.PARITY_NONE,
#                     stopbits=serial.STOPBITS_ONE,
#                     bytesize=serial.EIGHTBITS,
#                     timeout=5)

# 	# Discretization of the Teensy output voltage
# 	vlsb = vfsr / (2**precision)

# 	# Construct the TDC config commands
# 	wdata1_dict = dict(force_cal=1,
# 			parity_en=0,
# 			trigg_edge=0,
# 			stop_edge=0,
# 			start_edge=0,
# 			meas_mode=1,
# 			start_meas=1)
# 	wdata1 = tdc.construct_wdata1(**wdata1_dict)
# 	int_command1, int_wdata1 = tdc.construct_config(is_read=False, 
# 		addr=int(tdc.reg_addr_map['CONFIG1'], 16),
# 		wdata=wdata1)

# 	wdata2_dict = dict(calibration2_periods=1,
# 			avg_cycles=0,
# 			num_stop=4)
# 	wdata2 = tdc.construct_wdata2(**wdata2_dict)
# 	num_timers = tdc.code_numstop_map[wdata2_dict['num_stop']]
# 	int_command2, int_wdata2 = tdc.construct_config(is_read=False,
# 		addr=int(tdc.reg_addr_map['CONFIG2'], 16),
# 		wdata=wdata2)

# 	# # Get absolute voltages from common mode + differential voltages
# 	# vin_vec = []
# 	# for vincm, vdiff_vec in vtest_dict.items():
# 	# 	for vdiff in vdiff_vec:
# 	# 		vinp, vinn = spani_globals.vdiff_conv(vincm, vdiff)
# 	# 		vin_vec.append((vinp, vinn))

# 	# Iterate through all input voltage vinp-vinn pairs
# 	for vincm, vdiff_vec in vtest_dict.items():
# 		high_rate_vec = []
# 		for vdiff in vdiff_vec:
# 			vinp, vinn = spani_globals.vdiff_conv(vincm, vdiff)
# 			codep = int(round(vinp / vlsb))
# 			coden = int(round(vinn / vlsb))
			
# 			# tdiff_arr[i][j] is for the ith iteration of the jth timer pair
# 			# [
# 			# [t1-t0, t2-t1, t3-t2], <- iteration 0
# 			# [t1-t0, t2-t1, t3-t2], <- iteration 1
# 			# ...]
# 			# tdiff_arr = np.zeros((num_iterations, num_timers-1))
# 			tdiff_arr = [list() for _ in range(num_iterations)]
			
# 			# Take data over many iterations for the same input voltage pair
# 			for i in range(num_iterations):
# 				print(f'--- P/N: ({vinp}, {vinn}) -> Iteration {i}')
# 				# Reset and configure TDC connected to small signal chain
# 				teensy_ser.write(b'tdcsmallreset\n')
# 				print(teensy_ser.readline())

# 				teensy_ser.write(b'tdcsmallconfig\n')
# 				print(teensy_ser.readline())
# 				teensy_ser.write(int_command2.to_bytes(1, 'big'))
# 				teensy_ser.write(int_wdata2.to_bytes(1, 'big'))
# 				for _ in range(6):
# 					print(teensy_ser.readline())

# 				teensy_ser.write(b'tdcsmallconfig\n')
# 				print(teensy_ser.readline())
# 				teensy_ser.write(int_command1.to_bytes(1, 'big'))
# 				teensy_ser.write(int_wdata1.to_bytes(1, 'big'))
# 				for _ in range(6):
# 					print(teensy_ser.readline())

# 				# Set ZCD input voltages TODO check that integers parse correctly
# 				aux_ser.write(b'zcdcomppsmall\n')
# 				aux_ser.write(codep)
# 				aux_ser.write(b'zcdcompnsmall\n')
# 				aux_ser.write(coden)

# 				# Give the TDC a start pulse
# 				teensy_ser.write(b'tdcsmallstart\n')

# 				# Reading ALL the data
# 				teensy_ser.write(b'tdcsmallread\n')
# 				for _ in range(2):
# 					print(teensy_ser.readline())

# 				# ...for each timer output
# 				time_vec = [0]*6
# 				for timer_num, _ in enumerate(time_vec):
# 					# 1 byte (x3) at a time for the TIME registers
# 					val_time = 0
# 					for byte_num in range(3):
# 						time_bytes = teensy_ser.readline().strip()
# 						time_int = int.from_bytes(time_bytes, 
# 												byteorder='big',
# 												signed=False)
# 						val_time = val_time + (time_int << (byte_num*8))
# 					# Getting rid of parity bits, etc.
# 					time_vec[timer_num] = val_time % (1<<23) 

# 				# ...for each clock count
# 				clk_count_vec = [0]*5
# 				for clk_count_num, _ in enumerate(clk_count_vec):
# 					# 1 byte (x3) at a time for the CLOCK_COUNT registers
# 					val_count = 0
# 					for byte_num in range(3):
# 						count_bytes = teensy_ser.readline().strip()
# 						count_int = int.from_bytes(count_bytes,
# 												byteorder='big',
# 												signed=False)
# 						val_count = val_count + (count_int << (byte_num*8))
# 					# Getting rid of parity bits, etc.
# 					clk_count_vec[clk_count_num] = val_count % (1<<16)

# 				# ...for each calibration value
# 				cal_vec = [0]*2
# 				for cal_num, _ in enumerate(cal_vec):
# 					# 1 byte (x3) at a time for the CALIBRATION registers
# 					val_cal = 0
# 					for byte_num in range(3):
# 						cal_bytes = teensy_ser.readline().strip()
# 						cal_int = int.from_bytes(cal_bytes,
# 												byteorder='big',
# 												signed=False)
# 						val_cal = val_cal + (cal_int << (byte_num*8))
# 					# Getting rid of parity bits, etc.
# 					cal_vec[cal_num] = val_cal % (1<<23)

# 				# Final message from Teensy
# 				print(teensy_ser.readline())
				
# 				# Print statements for visibility
# 				print(f'Time: {time_vec}\n Cal: {cal_vec}\n Count: {clk_count_vec}')

# 				# Calculate the times of flight between each detected STOP pulse and
# 				# the START pulse
# 				tof_vec = []
# 				assert cal_vec[0] != cal_vec[1], f'Calibration data incorrect'

# 				time_x_vec = time_vec[:-1] if wdata1_dict['meas_mode'] == 0 else time_vec[1:]
# 				for j, time_x in enumerate(time_x_vec):
# 					tof_vec.append(tdc.calc_tof(cal1=cal_vec[0],
# 						cal2=cal_vec[1],
# 						cal2_periods=tdc.code_cal2_map[wdata2_dict['calibration2_periods']],
# 						time_1=time_vec[0],
# 						time_x=time_x,
# 						count_n=clk_count_vec[j],
# 						tper=tref_clk,
# 						mode=wdata1_dict['meas_mode']))

# 				# TODO change for efficiency - currently just throwing out 
# 				# irrelevant data, e.g. unused TIMEx data
# 				tof_vec = tof_vec[:num_timers]
# 				tdiff_vec = np.array(tof_vec[1:]) - np.array(tof_vec[:-1])

# 				# Throwing out overflow values
# 				# tdiff_vec = [tdiff for tdiff in tdiff_vec if tdiff > 0]
# 				tdiff_arr[i] = tdiff_vec

# 			# Find the average time between comparator noise-induced STOP triggers
# 			tdiff_avg = float(np.mean(tdiff_arr))
# 			high_rate_vec.append(0 if tdiff_avg == 0 else 1/tdiff_avg)
# 		high_rate_dict[float(vincm)] = dict(vdiff_vec=[float(vdiff) for vdiff in vdiff_vec],
# 											rate_vec=list(high_rate_vec))
# 	return high_rate_dict


def test_pk_static(teensy_port, aux_port, num_iterations, vtest_vec, vfsr=3.3, 
	precision=16, t_wait=0.01):
	'''
	Inputs:
		teensy_port: String. Name of the COM port the main board Teensy is 
			connected to.
		aux_port: String. Name of the COM port the auxiliary Teensy is connected
			to.
		num_iterations: Integer. Number of times to measure a single vtest.
		vtest_vec: Collection of ideal test voltages. These will be converted to 
			LSBs for the Teensy's analogWrite. Repeated values will be removed.
		vfsr: Float. The Teensy analogWrite full scale range in volts.
		precision: Integer. The number of bits to use in _both_ Teensies'
			analogRead and analogWrite.
		t_wait: Float. Time in seconds to wait between each iteration.
	Returns:
		vtest_real_dict: Dictionary with key:value of (ideal test voltage):
			(real test voltage given Teensy's precision restrictions).
		vtest_vout_dict: Dictionary with key:value (ideal vtest):(collection
			of output voltages)
	Notes:
		The argument for precision should match whatever's in the Teensy code!
	'''
	# Open serial connections
	teensy_ser = serial.Serial(port=teensy_port,
                    baudrate=19200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=1)

	aux_ser = serial.Serial(port=aux_port,
                    baudrate=19200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=10)

	# Discretization of the Teensy PWM
	vlsb = vfsr / (2**precision)

	# Take num_iterations readings from the main Teensy
	vtest_vout_dict = dict()
	vtest_real_dict = dict()
	for vtest in vtest_vec:
		vout_vec = []
		vtest_code = int(round(vtest/vlsb))
		vtest_real = vtest_code * vlsb

		# Trigger the auxiliary Teensy to get the ramp to
		# the target voltage
		aux_ser.write(b'peakslow\n')
		aux_ser.write(str(vtest_code).encode())
		print(aux_ser.readline())

		# Reset the peak detector
		# aux_ser.write(b'peakslow\n')
		# aux_ser.write(str(0).encode())
		# aux_ser.readline()
		teensy_ser.write(b'peakreset\n')

		# Take num_iterations readings at the same voltage
		for i in range(num_iterations):
			teensy_ser.write(b'peakread\n')
			vout_code = int(teensy_ser.readline())
			vout = vout_code / 2**precision * vfsr
			vout_vec.append(vout)
			time.sleep(t_wait)

		vtest_vout_dict[vtest] = vout_vec
		vtest_real_dict[vtest] = vtest_real
		print(f'{round(vtest,4)} \t {vtest_code} \t {round(vtest_real,4)} \t {[round(vout, 4) for vout in vout_vec]}')

	return vtest_real_dict, vtest_vout_dict

def test_dac(com_port, num_iterations, code_vec, dac_name, vfsr=3.3, 
	precision=16, t_wait=.001):
	'''
	Inputs:
		com_port: String. Name of the COM port to connect to.
		num_iterations: Integer. Number of times to measure a single code.
		code_vec: Collection of integers. Codes to measure.
		num_bits: Collection of bits.
		dac_name: Indicates which DAC is being tested, e.g. OUT_DAC_MAIN,
			OUT_DAC_SMALL, OUT_VDD_MAIN, OUT_VDD_AON
		vfsr: Float. Voltage full scale range of the Teensy analogRead.
		precision: Integer. Number of bits used by Teensy in analogRead. Note
			that this is set in the Teensy code, so this should be adjusted 
			in the Python to match.
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
		TODO GPIB for digital multimeter is wonky, hence the commented-out
			bits. Instead, it uses Teensy's analogRead.
		analogRead precision is set in the Teensy code, so the value of
			"precision" should be adjusted as necessary.
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

	# Take measurements, one step at a time
	for code in code_vec:
		# Convert code to binary for scan programming
		code_binary = [int(i) for i in list('{0:0b}'.format(code))] # MSB->LSB
		extra_zeros = [0]*(num_bits-len(code_binary)) # Zero padding as needed
		code_binary = extra_zeros + code_binary

		# Set scan bits
		en_main = 1 if dac_name in (spani_globals.OUT_DAC_MAIN, 
			spani_globals.OUT_VDD_MAIN, 
			spani_globals.OUT_REF_PREAMP) \
			else 0 
		en_small = 1 if dac_name in (spani_globals.OUT_DAC_SMALL, 
			spani_globals.OUT_VDD_SMALL) else 0

		construct_scan_params = {
			scan_arg_map[dac_name]: code_binary,
			'en_main' : [en_main],
			'en_small': [en_small]}
		
		# Program scan and temporarily suppress print statements
		# NB: zeroes everything but intended bits in scan
		try:
			spani_globals.block_print()
			scan_bits = scan.construct_ASC(**construct_scan_params)
			scan.program_scan(ser=teensy_ser, ASC=scan_bits)
			spani_globals.enable_print()
		except Exception as e:
			spani_globals.enable_print()
			raise e

		# Random blank prints that show up--not sure why
		for _ in range(2):
			teensy_ser.readline()

		# Take N=num_iterations measurements TODO
		for i in range(num_iterations):
			teensy_ser.write(teensy_arg_map[dac_name])
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
			print(f'Code/No. {code}/{i} -> {vout}')
			time.sleep(t_wait)

	# Close connection
	# vm.close()
	teensy_ser.close()
	return code_data_dict

def test_program_scan(com_port, ASC) -> None:
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
		bytesize=serial.EIGHTBITS,
		timeout=5)
	
	# Program Teensy, close if incorrect
	scan.program_scan(ser=ser, ASC=ASC)
	
	# Otherwise just close normally
	ser.close()

def temp_meas(tmp_port="", chamber_port="", 
	iterations=100, delay=1):
	'''
	Inputs:
        tmp_port: String. TMP102 Teensy COM port. Empty string if not used.
        chamber_port: String. Temperature chamber COM port. Empty string if not 
            used.
        iterations: Integer. Number of measurements to take. Note that
            the temperature will be sweeping over this time.
        delay: Float. Number of seconds to pause between readings.
    Returns:
        teensy_vec: List of floats. Internal temperature readings (C) from
            the Teensy. Contains "iterations" elements.
        tmp_vec: List of floats. Temperature readings (C) from the 
            ground truth TMP102 temperature sensor. Contains "iterations"
            elements if used, 0 otherwise.
        chamber_vec: List of floats. Temperature readings (C) from 
            the temperature chamber. Contains "iterations" elements if used,
            0 otherwise.
    Notes:
    	To use the TMP102, we use the Sparkfun TMP102 breakout board connected
    		to a Teensy using I2C. The Teensy is programmed using
    		temp_sensor.ino (in this repo).
    	The internal temperature is taken from the Teensy attached to the 
    		TMP102.
    	The temperature chamber is a TestEquity Model 107 using RS-232
    		for communication.
    	Return values are index-matched where applicable.
	'''
	use_TMP102 = bool(tmp_port)
	use_chamber = bool(chamber_port)

	assert use_TMP102 or use_chamber, "Must use TMP102 or chamber"

	teensy_vec = []
	tmp_vec = []
	chamber_vec = []

	# Open serial connections
	if use_TMP102:
		tmp_ser = serial.Serial(port=tmp_port,
			baudrate=19200,
			parity=serial.PARITY_NONE,
			stopbits=serial.STOPBITS_ONE,
			bytesize=serial.EIGHTBITS,
			timeout=1)
		print(tmp_ser.readline())
	if use_chamber:
		chamber_ser = minimalmodbus.Instrument(chamber_port, 1)
		chamber_ser.serial.baudrate = 9600

    # Sanity checking print statements
	disp_lst = []
	if use_TMP102:
		disp_lst.append('Teensy')
		disp_lst.append('TMP102')
	if use_chamber:
		disp_lst.append('Chamber')
	print('\t'.join(disp_lst))

	for i in range(iterations):
		if use_TMP102:
			# Read Teensy internal temp
			tmp_ser.write(b'tempinternal\n')
			teensy_val = float(tmp_ser.readline())

			# Read TMP102 temperature
			tmp_ser.write(b'temp\n')
			tmp_val = float(tmp_ser.readline())

			teensy_vec.append(teensy_val)
			tmp_vec.append(tmp_val)

		if use_chamber:
			chamber_val = temp_chamber.read_temp(chamber_ser)
			chamber_vec.append(chamber_val)

		# Printing relevant values with each reading for sanity check
		disp_lst = []
		if use_TMP102:
			disp_lst.append(str(teensy_val))
			disp_lst.append(str(tmp_val))
		if use_chamber:
			disp_lst.append(str(chamber_val))
		print('\t'.join(disp_lst))

		# Pause between readings
		time.sleep(delay)

	if use_TMP102:
		tmp_ser.close()

	if use_chamber:
			chamber_ser.serial.close()

	return teensy_vec, tmp_vec, chamber_vec

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
	scan.program_scan(com_port=teensy_port, ASC=asc)

	# Connect to function generator
	rm = pyvisa.ResourceManager()
	arb = rsrc_open(rm)

	# TODO Configure the function generator

	# TODO Turn on the output of the function generator

	# Turn off outputs and disconnect from function generator
	arb_close(arb)