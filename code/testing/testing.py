import pyvisa, serial, minimalmodbus
import time, sys, os
from dac import *
from gpib import *
import spani_globals, scan, temp_chamber, tdc
from pprint import pprint


def debug_tdiff_main(teensy_port, num_iterations, asc_params,
		vin_bias=0.8, vin_amp=0.2, tref_clk=1/15e6):
	'''
	Inputs:
	Returns:
	Notes:
	'''
	# Open connection to Teensy and Keysight 33500B
	teensy_ser = serial.Serial(port=tenesy_port,
			baudrate=19200,
			parity=serial.PARITY_NONE,
			stopbits=serial.STOPBITS_ONE,
			bytesize=serial.EIGHTBITS,
			timeout=5)

	rm = pyvisa.ResourceManager()
	arb = Keysight33500B(rm)
	arb.open_gpib()

	# TDC settings for measurement
	wdata1_dict = dict(
		force_cal=1,	# Get calibration
		parity_en=1,	# Enable parity bit in measurements
		trigg_edge=0, 	# Rising edge
		stop_edge=0, 	# Rising edge
		start_edge=0,	# Rising edge
		meas_mode=1,	# 0/1 somewhat deceptively assigned to Mode 1/2...
		start_meas=1)	# Arm TDC for measurement
	wdata1 = tdc.construct_wdata1(**wdata1_dict)

	cmd_cfg1, _ = tdc.construct_config(is_read=False, 
		addr=int(tdc.reg_addr_map['CONFIG1'], 16),
		wdata=wdata1)
	
	wdata2_dict = dict(
		calibration2_periods=1,	# -> 10 cycles wrt reference
		avg_cycles=0,			# No averaging
		num_stop=0 if wdata1_dict['meas_mode']==0 else 1)	# Single timer measurement
	wdata2 = tdc.construct_wdata2(**wdata2_dict)

	cmd_cfg2, _ = tdc.construct_config(is_read=False,
		addr=int(tdc.reg_addr_map['CONFIG2'], 16),
		wdata=wdata2)

	# Arb settings for measurement TODO
	cmd_lst = [
		"TRIG:SOUR:EXT",		# External trigger source
		"TRIG:SLOP POS",		# Trigger slope rising edge
		"TRIG:TIM:1E-5",		# 1us delay between trigger and output pulse
		"OUTP:SYNC:SOUR CH2",	# Set the sync output to channel 2
		""
		# "SOUR:2:FUNC:PULS",		# Switch Source 2 to pulse output
		]

	# Program the chip
	asc = scan.construct_ASC(**asc_params)
	scan.program_scan(ser=teensy_ser, ASC=asc)

	# Control the DG535
	for cmd in cmd_lst:
		arb.write(cmd)

	tdiff_vec = []

	for _ in range(num_iterations):
		# Reset the TDC
		# print('Resetting TDC')
		teensy_ser.write(b'tdcmainreset\n')
		# print(teensy_ser.readline())
		teensy_ser.readline()

		val_int_status = tdc.tdc_read(teensy_ser=teensy_ser,
			reg="INT_STATUS", chain="main")
		has_started = tdc.is_started(val_int_status)
		has_finished = tdc.is_done(val_int_status)
		has_ovfl_clk = tdc.is_overflow_clk(val_int_status)
		has_ovfl_coarse = tdc.is_overflow_coarse(val_int_status)

		assert not has_started, "Measurement shouldn't have started yet"

		# Configure the TDC
		# print('--- Configuring CONFIG1')
		teensy_ser.write(b'tdcmainconfig\n')
		teensy_ser.write(cmd_cfg1.to_bytes(1, 'big'))
		teensy_ser.write(wdata1.to_bytes(1, 'big'))
		for _ in range(5):
			# print(teensy_ser.readline())
			teensy_ser.readline()

		# print('--- Configuring CONFIG2')
		teensy_ser.write(b'tdcmainconfig\n')
		teensy_ser.write(cmd_cfg2.to_bytes(1, 'big'))
		teensy_ser.write(wdata2.to_bytes(1, 'big'))
		for _ in range(5):
			teensy_ser.readline()
			# print(teensy_ser.readline())

		# Feed in the start pulse to get things going
		# print('--- Feeding START')
		teensy_ser.write(b'tdcmainstart\n')
		# print(teensy_ser.readline())
		teensy_ser.readline()

		# Wait until measurement done
		has_finished = False
		while not has_finished:
			val_int_status = tdc.tdc_read(teensy_ser=teensy_ser,
				reg="INT_STATUS", chain="main")
			has_started = tdc.is_started(val_int_status)
			has_finished = tdc.is_done(val_int_status)
			has_ovfl_clk = tdc.is_overflow_clk(val_int_status)
			has_ovfl_coarse = tdc.is_overflow_coarse(val_int_status)

			assert has_started, "Measurement not properly initialized"

		# Read from relevant data registers
		num_timers = tdc.code_numstop_map[wdata2_dict['num_stop']]
		reg_lst = ['CALIBRATION1', 'CALIBRATION2']
		reg_lst = reg_lst + [f'TIME{i}' for i in range(1,num_timers+1)]
		reg_lst = reg_lst + [f'CLOCK_COUNT{i}' for i in range(1,num_timers+1)]

		reg_data_dict = dict()
		for reg in reg_lst:
			reg_data_dict[reg] = tdc.tdc_read(teensy_ser=teensy_ser,
				reg=reg, chain="main")
			# print(f'-> {reg_data_dict[reg]}')

		# From registers, calculate the time between the START and STOP triggers
		time_x_reg = 'TIME1' if wdata1_dict['meas_mode'] == 0 else 'TIME2'

		tdiff = tdc.calc_tof(
			cal1=reg_data_dict['CALIBRATION1'] % (1<<23),
			cal2=reg_data_dict['CALIBRATION2'] % (1<<23),
			cal2_periods=tdc.code_cal2_map[wdata2_dict['calibration2_periods']],
			time_1=reg_data_dict['TIME1'] % (1<<23),
			time_x=reg_data_dict[time_x_reg] % (1<<23),
			count_n=reg_data_dict['CLOCK_COUNT1'] % (1<<16),
			tper=tref_clk,
			mode=wdata1_dict['meas_mode'])

		print(f'\t\t {tdiff}')
		tdiff_vec.append(tdiff)

	# Close connections
	teensy_ser.close()
	arb.close()

	return tdiff_vec


def test_tdiff_main(teensy_port, num_iterations, asc_params,
	 	ip_addr='192.168.4.1', gpib_addr=15, 
		vin_bias=0.8, vin_amp=0.2, tref_clk=1/15e6):
	'''
	Measures the time between the input DG535 pulse and the output pulse.
	Inputs:
		teensy_port: String. Name of the COM port the main board Teensy is 
			connected to.
		num_iterations: Integer. Number of times to measure for a single
			amplitude.
		asc_params: Dictionary of collections of integers, used in
			programming the scan chain. See scan.construct_asc.
		twait: Float. Time in seconds between measurement start and actual 
			DG535 trigger. e.g. twait = 1e-9 means the DG535 triggers 1ns after
			the measurement actually starts.
		tdelay: Float. Time in seconds to delay the input pulse.
		ip_addr: String. The IP address of the Prologix hooked up
			to the DG535.
		gpib_addr: Integer. The GPIB address associated with the DG535.
		vin_bias: Float. Input bias in V for the input pulse.
		vin_amp: Float. Pulse amplitude in V for the signal shaping.
		tref_clk: Float. Period in seconds of the TDC reference clock.
	Returns:
		tdiff_vec: Collection of floats. The time difference (in seconds) 
			between the input DG535 pulse and output pulse.
	Notes:
		Within the analog scan chain, you'll likely need to set
			Attenuator reference voltage (mandatory)
			Preamplifier reference voltage
			DAC voltage
		See <overleaf link> to figure out how things are meant to be wired up.
	'''
	# Open connections to Teensy and DG535
	teensy_ser = serial.Serial(port=teensy_port,
                    baudrate=19200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=5)

	rm = pyvisa.ResourceManager()
	dg535 = DG535(rm)
	dg535.open_prologix(ip_addr=ip_addr, gpib_addr=gpib_addr)

	# Sanity checking DG535 status
	dg535.write("CL")
	print(f"Error Status: {dg535.query('ES')}")
	print(f"Instrument Status: {dg535.query('IS')}")

	# TDC settings for measurement
	wdata1_dict = dict(
		force_cal=1,	# Get calibration
		parity_en=1,	# Enable parity bit in measurements
		trigg_edge=0, 	# Rising edge
		stop_edge=0, 	# Rising edge
		start_edge=0,	# Rising edge
		meas_mode=0,	# 0/1 somewhat deceptively assigned to Mode 1/2...
		start_meas=1)	# Arm TDC for measurement
	wdata1 = tdc.construct_wdata1(**wdata1_dict)

	cmd_cfg1, _ = tdc.construct_config(is_read=False, 
		addr=int(tdc.reg_addr_map['CONFIG1'], 16),
		wdata=wdata1)
	
	wdata2_dict = dict(
		calibration2_periods=1,	# -> 10 cycles wrt reference
		avg_cycles=0,			# No averaging
		num_stop=0 if wdata1_dict['meas_mode']==0 else 1)	# Single timer measurement
	wdata2 = tdc.construct_wdata2(**wdata2_dict)

	cmd_cfg2, _ = tdc.construct_config(is_read=False,
		addr=int(tdc.reg_addr_map['CONFIG2'], 16),
		wdata=wdata2)

	# DG535 settings for measurement
	# - Channel T0 comes roughly 85ns after TRIG is received
	cmd_lst = [
		"TM 1",						# External trigger
		"TS 1",						# Rising edge trigger
		"TL 1.00",					# Edge trigger level
		"TZ 0,1",					# Trigger is high impedance
		# "TZ 1,1",					# T0 termination HiZ
		"TZ 1,0",					# T0 termination 50Ohm
		"OM 1,3",					# T0 output VARiable
		f"OA 1,{vin_amp}",			# T0 channel amplitude
		f"OO 1,{vin_bias}",			# T0 channel offset
	]

	# Program the chip
	asc = scan.construct_ASC(**asc_params)
	scan.program_scan(ser=teensy_ser, ASC=asc)

	# Control the DG535
	for cmd in cmd_lst:
		dg535.write(cmd)

	tdiff_vec = []

	for _ in range(num_iterations):
		# Reset the TDC
		# print('Resetting TDC')
		teensy_ser.write(b'tdcmainreset\n')
		# print(teensy_ser.readline())
		teensy_ser.readline()

		val_int_status = tdc.tdc_read(teensy_ser=teensy_ser,
			reg="INT_STATUS", chain="main")
		has_started = tdc.is_started(val_int_status)
		has_finished = tdc.is_done(val_int_status)
		has_ovfl_clk = tdc.is_overflow_clk(val_int_status)
		has_ovfl_coarse = tdc.is_overflow_coarse(val_int_status)

		# Sanity checking with some visibility
		# print(f'\t Measurement Started: {has_started}')
		# print(f'\t Measurement Done: {has_finished}')
		# print(f'\t Clock Overflow: {has_ovfl_clk}')
		# print(f'\t Coarse Overflow: {has_ovfl_coarse}')
		# print(f'-> {val_int_status}')

		assert not has_started, "Measurement shouldn't have started yet"

		# Configure the TDC
		# print('--- Configuring CONFIG1')
		teensy_ser.write(b'tdcmainconfig\n')
		teensy_ser.write(cmd_cfg1.to_bytes(1, 'big'))
		teensy_ser.write(wdata1.to_bytes(1, 'big'))
		for _ in range(5):
			# print(teensy_ser.readline())
			teensy_ser.readline()

		# print('--- Configuring CONFIG2')
		teensy_ser.write(b'tdcmainconfig\n')
		teensy_ser.write(cmd_cfg2.to_bytes(1, 'big'))
		teensy_ser.write(wdata2.to_bytes(1, 'big'))
		for _ in range(5):
			teensy_ser.readline()
			# print(teensy_ser.readline())

		# Feed in the start pulse to get things going
		# print('--- Feeding START')
		teensy_ser.write(b'tdcmainstart\n')
		# print(teensy_ser.readline())
		teensy_ser.readline()

		# Wait until measurement done
		has_finished = False
		while not has_finished:
			val_int_status = tdc.tdc_read(teensy_ser=teensy_ser,
				reg="INT_STATUS", chain="main")
			has_started = tdc.is_started(val_int_status)
			has_finished = tdc.is_done(val_int_status)
			has_ovfl_clk = tdc.is_overflow_clk(val_int_status)
			has_ovfl_coarse = tdc.is_overflow_coarse(val_int_status)

			# Sanity checking with some visibility
			# print(f'\t Measurement Started: {has_started}')
			# print(f'\t Measurement Done: {has_finished}')
			# print(f'\t Clock Overflow: {has_ovfl_clk}')
			# print(f'\t Coarse Overflow: {has_ovfl_coarse}')
			# print(f'-> {val_int_status}')

			assert has_started, "Measurement not properly initialized"

		# Read from relevant data registers
		num_timers = tdc.code_numstop_map[wdata2_dict['num_stop']]
		reg_lst = ['CALIBRATION1', 'CALIBRATION2']
		reg_lst = reg_lst + [f'TIME{i}' for i in range(1,num_timers+1)]
		reg_lst = reg_lst + [f'CLOCK_COUNT{i}' for i in range(1,num_timers+1)]

		reg_data_dict = dict()
		for reg in reg_lst:
			reg_data_dict[reg] = tdc.tdc_read(teensy_ser=teensy_ser,
				reg=reg, chain="main")
			# print(f'-> {reg_data_dict[reg]}')

		# From registers, calculate the time between the START and STOP triggers
		time_x_reg = 'TIME1' if wdata1_dict['meas_mode'] == 0 else 'TIME2'

		tdiff = tdc.calc_tof(
			cal1=reg_data_dict['CALIBRATION1'] % (1<<23),
			cal2=reg_data_dict['CALIBRATION2'] % (1<<23),
			cal2_periods=tdc.code_cal2_map[wdata2_dict['calibration2_periods']],
			time_1=reg_data_dict['TIME1'] % (1<<23),
			time_x=reg_data_dict[time_x_reg] % (1<<23),
			count_n=reg_data_dict['CLOCK_COUNT1'] % (1<<16),
			tper=tref_clk,
			mode=wdata1_dict['meas_mode'])

		print(f'\t\t {tdiff}')
		tdiff_vec.append(tdiff)

	# Close connections
	teensy_ser.close()
	dg535.close_prologix()

	return tdiff_vec


def test_fflvl_jitter(teensy_port, num_iterations, twait=250e-9,
		ip_addr='192.168.1.4', gpib_addr=15, tref_clk=1/15e6):
	'''
	Measures the time between the input DG535 pulse and the output pulse 
	that comes from the board-level components. This is intended 
	to measure the jitter of board-level components, so I highly recommend
	using this on a board that does not have a functional chip on it.
	Inputs:
		teensy_port: String. Name of the COM port the main board Teensy is 
			connected to.
		num_iterations: Integer. Number of times to measure for a single
			amplitude.
		twait: Float. Time in seconds between measurement start and actual 
			DG535 trigger. e.g. twait = 1e-9 means the DG535 triggers 1ns after
			the measurement actually starts.
		ip_addr: String. The IP address of the Prologix hooked up
			to the DG535.
		gpib_addr: Integer. The GPIB address associated with the DG535.
		vin_bias: Float. Input bias in V for the input pulse.
		vin_amp: Float. Pulse amplitude in V for the signal shaping.
		tref_clk: Float. Period in seconds of the TDC reference clock.
	Returns:
		tdiff_vec: Collection of floats. The time difference (in seconds) 
			between the input DG535 pulse and output pulse.
	Notes:
		See <overleaf link> to figure out how things are meant to be wired up.

	'''
	# Open connections to Teensy and DG535
	teensy_ser = serial.Serial(port=teensy_port,
                    baudrate=19200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=5)

	rm = pyvisa.ResourceManager()
	dg535 = DG535(rm)
	dg535.open_prologix(ip_addr=ip_addr, gpib_addr=gpib_addr)

	# Sanity checking DG535 status
	dg535.write("CL")
	print(f"Error Status: {dg535.query('ES')}")
	print(f"Instrument Status: {dg535.query('IS')}")

	# TDC settings for measurement
	wdata1_dict = dict(
		force_cal=1,	# Get calibration
		parity_en=1,	# Enable parity bit in measurements
		trigg_edge=0, 	# Rising edge
		stop_edge=0, 	# Rising edge
		start_edge=0,	# Rising edge
		meas_mode=0,	# Somewhat deceptively assigned to Mode 2...
		start_meas=1)	# Arm TDC for measurement
	wdata1 = tdc.construct_wdata1(**wdata1_dict)

	cmd_cfg1, _ = tdc.construct_config(is_read=False, 
		addr=int(tdc.reg_addr_map['CONFIG1'], 16),
		wdata=wdata1)
	
	wdata2_dict = dict(
		calibration2_periods=1,	# -> 10 cycles wrt reference
		avg_cycles=0,			# No averaging
		num_stop=0)				# Single timer measurement
	wdata2 = tdc.construct_wdata2(**wdata2_dict)

	cmd_cfg2, _ = tdc.construct_config(is_read=False,
		addr=int(tdc.reg_addr_map['CONFIG2'], 16),
		wdata=wdata2)

	# DG535 settings for measurement
	# Channel A = main signal, also passes through attenuator
	cmd_lst = [
		"TM 1",						# External trigger
		"TS 1",						# Rising edge trigger
		"TL 1.00",					# Edge trigger level
		"TZ 0,1",					# Trigger is high impedance
		f"DT 2,1,{twait}", 			# Set delay A=T0+twait
		"TZ 1,1",					# T0 termination HiZ
		"TZ 2,1",					# A termination HiZ
		"OM 1,3",					# T0 output VARiable
		"OM 2,3",					# A output VARiable
		f"OA 2,1.8",				# A channel amplitude
		f"OA 1,3.3",				# T0 channel amplitude
		f"OO 2,0",					# A channel offset
		f"OO 1,0",					# T0 channel offset
	]

	# Control the DG535
	for cmd in cmd_lst:
		dg535.write(cmd)

	tdiff_vec = []

	for _ in range(num_iterations):
		# Reset the TDC until it actually resets
		has_started = True
		count = 0
		while has_started and count < 10:
			print('Resetting TDC')
			teensy_ser.write(b'tdcsmallreset\n')
			print(teensy_ser.readline())

			val_int_status = tdc.tdc_read(teensy_ser=teensy_ser,
				reg="INT_STATUS", chain="small")
			has_started = tdc.is_started(val_int_status)
			has_finished = tdc.is_done(val_int_status)
			has_ovfl_clk = tdc.is_overflow_clk(val_int_status)
			has_ovfl_coarse = tdc.is_overflow_coarse(val_int_status)

			# Sanity checking with some visibility
			print(f'\t Measurement Started: {has_started}')
			print(f'\t Measurement Done: {has_finished}')
			print(f'\t Clock Overflow: {has_ovfl_clk}')
			print(f'\t Coarse Overflow: {has_ovfl_coarse}')
			print(f'-> {val_int_status}')

			count = count + 1


		assert not has_started, "Measurement shouldn't have started yet"

		# Configure the TDC
		print('--- Configuring CONFIG1')
		teensy_ser.write(b'tdcsmallconfig\n')
		teensy_ser.write(cmd_cfg1.to_bytes(1, 'big'))
		teensy_ser.write(wdata1.to_bytes(1, 'big'))
		for _ in range(5):
			print(teensy_ser.readline())

		print('--- Configuring CONFIG2')
		teensy_ser.write(b'tdcsmallconfig\n')
		teensy_ser.write(cmd_cfg2.to_bytes(1, 'big'))
		teensy_ser.write(wdata2.to_bytes(1, 'big'))
		for _ in range(5):
			print(teensy_ser.readline())

		# Feed in the start pulse to get things going - may need more than once
		count = 0
		while not has_started and count < 10:
			print('--- Feeding START')
			teensy_ser.write(b'tdcsmallstart\n')
			print(teensy_ser.readline())

			val_int_status = tdc.tdc_read(teensy_ser=teensy_ser,
				reg="INT_STATUS", chain="small")
			has_started = tdc.is_started(val_int_status)
			count = count + 1

		# Wait until measurement done
		has_finished = False
		while not has_finished:
			val_int_status = tdc.tdc_read(teensy_ser=teensy_ser,
				reg="INT_STATUS", chain="small")
			has_started = tdc.is_started(val_int_status)
			has_finished = tdc.is_done(val_int_status)
			has_ovfl_clk = tdc.is_overflow_clk(val_int_status)
			has_ovfl_coarse = tdc.is_overflow_coarse(val_int_status)

			# Sanity checking with some visibility
			print(f'\t Measurement Started: {has_started}')
			print(f'\t Measurement Done: {has_finished}')
			print(f'\t Clock Overflow: {has_ovfl_clk}')
			print(f'\t Coarse Overflow: {has_ovfl_coarse}')
			print(f'-> {val_int_status}')

			assert has_started, "Measurement not properly initialized"

		# Read from relevant data registers
		num_timers = tdc.code_numstop_map[wdata2_dict['num_stop']]
		reg_lst = ['CALIBRATION1', 'CALIBRATION2']
		reg_lst = reg_lst + [f'TIME{i}' for i in range(1,num_timers+1)]
		reg_lst = reg_lst + [f'CLOCK_COUNT{i}' for i in range(1,num_timers+1)]

		reg_data_dict = dict()
		for reg in reg_lst:
			reg_data_dict[reg] = tdc.tdc_read(teensy_ser=teensy_ser,
				reg=reg, chain="small")
			print(f'-> {reg_data_dict[reg]}')

		# From registers, calculate the time between the START and STOP triggers
		tdiff = tdc.calc_tof(
			cal1=reg_data_dict['CALIBRATION1'] % (1<<23),
			cal2=reg_data_dict['CALIBRATION2'] % (1<<23),
			cal2_periods=tdc.code_cal2_map[wdata2_dict['calibration2_periods']],
			time_1=reg_data_dict['TIME1'] % (1<<23),
			time_x=reg_data_dict['TIME1'] % (1<<23),
			count_n=reg_data_dict['CLOCK_COUNT1'] % (1<<16),
			tper=tref_clk,
			mode=wdata1_dict['meas_mode'])

		print(f'\t\t {tdiff}')
		tdiff_vec.append(tdiff)

	# Close connections
	teensy_ser.close()
	dg535.close_prologix()

	return tdiff_vec


def test_tdiff_small(teensy_port, num_iterations, asc_params,
	 	ip_addr='192.168.4.1', gpib_addr=15, 
		vin_bias=0.7, vin_amp=0.6, tref_clk=1/15e6):
	'''
	Measures the time between the input DG535 pulse and the output pulse.
	Inputs:
		teensy_port: String. Name of the COM port the main board Teensy is 
			connected to.
		num_iterations: Integer. Number of times to measure for a single
			amplitude.
		asc_params: Dictionary of collections of integers, used in
			programming the scan chain. See scan.construct_asc.
		twait: Float. Time in seconds between measurement start and actual 
			DG535 trigger. e.g. twait = 1e-9 means the DG535 triggers 1ns after
			the measurement actually starts.
		tdelay: Float. Time in seconds to delay the input pulse.
		ip_addr: String. The IP address of the Prologix hooked up
			to the DG535.
		gpib_addr: Integer. The GPIB address associated with the DG535.
		vin_bias: Float. Input bias in V for the input pulse.
		vin_amp: Float. Pulse amplitude in V for the signal shaping.
		tref_clk: Float. Period in seconds of the TDC reference clock.
	Returns:
		tdiff_vec: Collection of floats. The time difference (in seconds) 
			between the input DG535 pulse and output pulse.
	Notes:
		See <overleaf link> to figure out how things are meant to be wired up.
	'''
	# Open connections to Teensy and DG535
	teensy_ser = serial.Serial(port=teensy_port,
                    baudrate=19200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=5)

	rm = pyvisa.ResourceManager()
	dg535 = DG535(rm)
	dg535.open_prologix(ip_addr=ip_addr, gpib_addr=gpib_addr)

	# Sanity checking DG535 status
	dg535.write("CL")
	print(f"Error Status: {dg535.query('ES')}")
	print(f"Instrument Status: {dg535.query('IS')}")

	# TDC settings for measurement
	wdata1_dict = dict(
		force_cal=1,	# Get calibration
		parity_en=1,	# Enable parity bit in measurements
		trigg_edge=0, 	# Rising edge
		stop_edge=0, 	# Rising edge
		start_edge=0,	# Rising edge
		meas_mode=0,	# Somewhat deceptively assigned to Mode 2...
		start_meas=1)	# Arm TDC for measurement
	wdata1 = tdc.construct_wdata1(**wdata1_dict)

	cmd_cfg1, _ = tdc.construct_config(is_read=False, 
		addr=int(tdc.reg_addr_map['CONFIG1'], 16),
		wdata=wdata1)
	
	wdata2_dict = dict(
		calibration2_periods=1,	# -> 10 cycles wrt reference
		avg_cycles=0,			# No averaging
		num_stop=0 if wdata1_dict['meas_mode']==0 else 1)	# Single timer measurement
	wdata2 = tdc.construct_wdata2(**wdata2_dict)

	cmd_cfg2, _ = tdc.construct_config(is_read=False,
		addr=int(tdc.reg_addr_map['CONFIG2'], 16),
		wdata=wdata2)

	# DG535 settings for measurement
	# - Channel T0 comes roughly 85ns after TRIG is received
	# - It branches 3 ways--unaltered, delayed, and attenuated
	cmd_lst = [
		"TM 1",						# External trigger
		"TS 1",						# Rising edge trigger
		"TL 1.00",					# Edge trigger level
		"TZ 0,1",					# Trigger is high impedance
		"TZ 1,1",					# T0 termination HiZ
		# "TZ 1,0",					# T0 termination 50Ohm
		"OM 1,3",					# T0 output VARiable
		f"OA 1,{vin_amp}",			# T0 channel amplitude
		f"OO 1,{vin_bias}",			# T0 channel offset
	]

	# Program the chip
	asc = scan.construct_ASC(**asc_params)
	scan.program_scan(ser=teensy_ser, ASC=asc)

	# Control the DG535
	for cmd in cmd_lst:
		dg535.write(cmd)

	tdiff_vec = []

	for _ in range(num_iterations):
		# Reset the TDC
		# print('Resetting TDC')
		teensy_ser.write(b'tdcsmallreset\n')
		# print(teensy_ser.readline())
		teensy_ser.readline()

		val_int_status = tdc.tdc_read(teensy_ser=teensy_ser,
			reg="INT_STATUS", chain="small")
		has_started = tdc.is_started(val_int_status)
		has_finished = tdc.is_done(val_int_status)
		has_ovfl_clk = tdc.is_overflow_clk(val_int_status)
		has_ovfl_coarse = tdc.is_overflow_coarse(val_int_status)

		# Sanity checking with some visibility
		# print(f'\t Measurement Started: {has_started}')
		# print(f'\t Measurement Done: {has_finished}')
		# print(f'\t Clock Overflow: {has_ovfl_clk}')
		# print(f'\t Coarse Overflow: {has_ovfl_coarse}')
		# print(f'-> {val_int_status}')

		assert not has_started, "Measurement shouldn't have started yet"

		# Configure the TDC
		# print('--- Configuring CONFIG1')
		teensy_ser.write(b'tdcsmallconfig\n')
		teensy_ser.write(cmd_cfg1.to_bytes(1, 'big'))
		teensy_ser.write(wdata1.to_bytes(1, 'big'))
		for _ in range(5):
			# print(teensy_ser.readline())
			teensy_ser.readline()

		# print('--- Configuring CONFIG2')
		teensy_ser.write(b'tdcsmallconfig\n')
		teensy_ser.write(cmd_cfg2.to_bytes(1, 'big'))
		teensy_ser.write(wdata2.to_bytes(1, 'big'))
		for _ in range(5):
			teensy_ser.readline()
			# print(teensy_ser.readline())

		# Feed in the start pulse to get things going
		# print('--- Feeding START')
		teensy_ser.write(b'tdcsmallstart\n')
		# print(teensy_ser.readline())
		teensy_ser.readline()

		# Wait until measurement done
		has_finished = False
		while not has_finished:
			val_int_status = tdc.tdc_read(teensy_ser=teensy_ser,
				reg="INT_STATUS", chain="small")
			has_started = tdc.is_started(val_int_status)
			has_finished = tdc.is_done(val_int_status)
			has_ovfl_clk = tdc.is_overflow_clk(val_int_status)
			has_ovfl_coarse = tdc.is_overflow_coarse(val_int_status)

			# Sanity checking with some visibility
			# print(f'\t Measurement Started: {has_started}')
			# print(f'\t Measurement Done: {has_finished}')
			# print(f'\t Clock Overflow: {has_ovfl_clk}')
			# print(f'\t Coarse Overflow: {has_ovfl_coarse}')
			# print(f'-> {val_int_status}')

			assert has_started, "Measurement not properly initialized"

		# Read from relevant data registers
		num_timers = tdc.code_numstop_map[wdata2_dict['num_stop']]
		reg_lst = ['CALIBRATION1', 'CALIBRATION2']
		reg_lst = reg_lst + [f'TIME{i}' for i in range(1,num_timers+1)]
		reg_lst = reg_lst + [f'CLOCK_COUNT{i}' for i in range(1,num_timers+1)]

		reg_data_dict = dict()
		for reg in reg_lst:
			reg_data_dict[reg] = tdc.tdc_read(teensy_ser=teensy_ser,
				reg=reg, chain="small")
			# print(f'-> {reg_data_dict[reg]}')

		# From registers, calculate the time between the START and STOP triggers
		time_x_reg = 'TIME1' if wdata1_dict['meas_mode'] == 0 else 'TIME2'

		tdiff = tdc.calc_tof(
			cal1=reg_data_dict['CALIBRATION1'] % (1<<23),
			cal2=reg_data_dict['CALIBRATION2'] % (1<<23),
			cal2_periods=tdc.code_cal2_map[wdata2_dict['calibration2_periods']],
			time_1=reg_data_dict['TIME1'] % (1<<23),
			time_x=reg_data_dict[time_x_reg] % (1<<23),
			count_n=reg_data_dict['CLOCK_COUNT1'] % (1<<16),
			tper=tref_clk,
			mode=wdata1_dict['meas_mode'])

		print(f'\t\t {tdiff}')
		tdiff_vec.append(tdiff)

	# Close connections
	teensy_ser.close()
	dg535.close_prologix()

	return tdiff_vec

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
			meas_mode=0,
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
	precision=16):
	'''
	Inputs:
		com_port: String. Name of the COM port to connect to.
		num_iterations: Integer. Number of times to measure a single code.
		code_vec: Collection of integers. Codes to measure.
		num_bits: Collection of bits.
		dac_name: Indicates which DAC is being tested, e.g. spani_globals.OUT_DAC_MAIN,
			OUT_DAC_SMALL, OUT_VDD_MAIN, OUT_VDD_AON
		vfsr: Float. Voltage full scale range of the Teensy analogRead.
		precision: Integer. Number of bits used by Teensy in analogRead. Note
			that this is set in the Teensy code, so this should be adjusted 
			in the Python to match.
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
			try:
				cout = int(teensy_ser.readline())
				vout = vfsr * cout / (2**precision)
			except Exception as e:
				print(e)
				vout = float('nan')
			code_data_dict[code].append(vout)
			print(f'Code/No. {code}/{i} -> {vout}')

	# Close connection
	teensy_ser.close()
	return code_data_dict

def get_vref_atten_target(com_port, num_iterations, vfsr=3.3, precision=16):
	'''
	Reads the voltage on the VREF_ATTEN pin num_iterations times and spits
		out the voltage in volts.
	Inputs:
		com_port: String. Name of the COM port to connect to.
		num_iterations: Integer. Number of times to measure a single code.
		precision: Integer. Number of bits used by Teensy in analogRead. Note
			that this is set in the Teensy code, so this should be adjusted 
			in the Python to match.
	Returns:
		vout: Float. The target voltage for the attenuator, measured from the unloaded
			pin.
		code: Integer. The code associated with the output voltage.
	Notes:
		This assumes that your scan chain has been set appropriately already.
	'''
	# Open serial connection to Teensy
	teensy_ser = serial.Serial(port=com_port,
                    baudrate=19200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=1)

	# Multiple readings to deal with noise
	vout_vec = []
	cout_vec = []
	for _ in range(num_iterations):
		# Read the voltage in LSB and convert to voltage
		teensy_ser.write(b'attenread\n')
		try:
			cout = int(teensy_ser.readline())
			vout = vfsr * cout / (2**precision)
		except Exception as e:
			print(e)
			vout = float('nan')

		cout_vec.append(cout)
		vout_vec.append(vout)

	# Close connections
	teensy_ser.close()

	return np.mean(vout_vec), int(round(np.mean(cout_vec)))

def get_dac_code(com_port, num_iterations, vdac_target, dac_name, vfsr=3.3,
	precision=16) -> int:
	'''
	Inputs:
		com_port: String. Name of the COM port to connect to.
		num_iterations: Integer. Number of times to measure a single code.
		vdac_target: Float. The target voltage for the DAC.
		num_bits: Collection of bits.
		dac_name: Indicates which DAC is being tested, e.g. spani_globals.OUT_DAC_MAIN,
			OUT_DAC_SMALL, OUT_VDD_MAIN, OUT_VDD_AON
		vfsr: Float. Voltage full scale range of the Teensy analogRead.
		precision: Integer. Number of bits used by Teensy in analogRead. Note
			that this is set in the Teensy code, so this should be adjusted 
			in the Python to match.
	Returns:
		result: The code most closely associated with the target voltage.
	Raises:
		AssertionError: If a code in the collection of codes exceeds the
			number of bits permitted.
	Notes:
		Performs a linear search of DAC code to find which one most 
			closely matches the target voltage. This does not assume
			that the DAC is monotonic.
		analogRead precision is set in the Teensy code, so the value of
			"precision" should be adjusted here to match whatever the
			Teensy has.
	'''
	# Sweep through the DAC codes (doesn't assume monotonicity)
	num_bits = spani_globals.N_BITS_MAP[dac_name]
	code_max = 1 << num_bits
	code_data_dict = test_dac(com_port=com_port, 
		num_iterations=num_iterations,
		code_vec=range(code_max),
		dac_name=dac_name,
		vfsr=vfsr,
		precision=precision,
		t_wait=0)

	# Find the code which gets the closest match in voltage
	code_vec = code_data_dict.keys()
	avg_vec = [np.mean(code_data_dict[code]) for code in code_vec]
	diff_vec = [abs(vout-vdac_target) for vout in avg_vec]

	idx_closest = np.argmin(diff_vec)
	return code_vec[idx_closest]

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