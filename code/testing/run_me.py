import serial, pyvisa, minimalmodbus
import numpy as np
import random
from datetime import date, datetime
import os, sys, time, pdb, traceback
import csv, yaml
from gpib import *

import spani_globals, scan, bandgap, testing, plotting

def run_main():
	timestamp = datetime.now()
	timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")

	####################
	### Program Scan ###
	####################
	if False:
		teensy_port = 'COM5'
		asc_params = dict(
			# MSB -> LSB
			preamp_res 		= [0, 0],
			delay_res 		= [0, 0],
			watchdog_res 	= [0, 0, 0, 0],
			attenuator_sel	= [0, 0, 0],
			dac_sel 		= [0, 0, 0, 0, 0, 0, 0, 0],
			az_main_gain 	= [0, 0, 0],
			az_aux_gain 	= [0, 0, 0],
			oneshot_res 	= [0, 0],
			vref_preamp 	= [0, 0, 0, 0, 0, 0, 0, 0],
			vdd_aon			= [1, 1, 1, 1, 1],
			vdd_signal		= [1, 1, 1, 1, 1],
			en_main			= [1],
			en_small		= [1])

		print("Constructing scan chain...")
		asc = scan.construct_ASC(**asc_params)
		# asc = [1, 1] * 22
		print(f"Programming scan...{asc}")
		testing.test_program_scan(com_port=teensy_port, ASC=asc)

	############
	### DACs ###
	############
	if False:
		which_dac = spani_globals.OUT_REF_PREAMP
		test_dac_params = dict(
			com_port='COM5',
			num_iterations=100,
			code_vec=range(0, int(2**spani_globals.N_BITS_MAP[which_dac]), 10),
			dac_name=which_dac,
			vfsr=3.3,
			precision=16,
			t_wait=.001)

		dac_data = testing.test_dac(**test_dac_params)

		# Dump the output into a human-readable file
		file_out = f'../../data/testing/{timestamp_str}_dac{which_dac}_{test_dac_params["num_iterations"]}x.csv'
		with open(file_out, 'w', newline='') as csvfile:
			fwriter = csv.writer(csvfile, delimiter=",",
				quotechar="|", quoting=csv.QUOTE_MINIMAL)
			fwriter.writerow(['Code']+[f'Iteration {i}' for i in range(1, num_iterations+1)])
			for code, lsb_vec in dac_data.items():
				fwriter.writerow([code] + list(lsb_vec))

	###############################
	### Bandgap in Temp Chamber ###
	###############################
	if False:
		bandgap_meas_params = dict(
			teensy_port 		= 'COM3', 
			temp_port 			= '',
			chamber_port 		= 'COM4',
			teensy_precision 	= 16,
			vfsr 				= 3.3,
			iterations 			= 10800,
			delay 				= 1)
		file_out = f'../../data/testing/{timestamp_str}_bandgap_{bandgap_meas_params["iterations"]}x.csv'
		teensy_vec, temp_vec, chamber_vec, vbg_vec = bandgap.get_data(**bandgap_meas_params)

		with open(file_out, 'w', newline='') as csvfile:
			fwriter = csv.writer(csvfile, delimiter=",", 
				quotechar="|", quoting=csv.QUOTE_MINIMAL)
			fwriter.writerow(['Teensy Internal Temp'] + teensy_vec)
			fwriter.writerow(['TMP102'] + temp_vec)
			fwriter.writerow(['Chamber'] + chamber_vec)
			fwriter.writerow(['Bandgap (V)'] + vbg_vec)

	########################################
	### Various Temperature Measurements ###
	########################################
	if False:
		teensy_vec, tmp_vec, chamber_vec = testing.temp_meas(
			tmp_port="COM3",
			chamber_port="COM4",
			iterations=7200,
			delay=1)

		file_out = f'../../data/testing/{timestamp_str}_temp.csv'
		with open(file_out, 'w', newline='') as csvfile:
			fwriter = csv.writer(csvfile, delimiter=",", 
				quotechar="|", quoting=csv.QUOTE_MINIMAL)
			fwriter.writerow(['Teensy Internal Temp'] + teensy_vec)
			fwriter.writerow(['TMP102'] + tmp_vec)
			fwriter.writerow(['Chamber'] + chamber_vec)

	##################################
	### Peak Detector Static Error ###
	##################################
	if False:
		pk_static_params = dict(teensy_port="COM5",
			aux_port="COM3",
			num_iterations=200,
			vfsr=3.3,
			precision=16,
			t_wait=.1)
		vlsb = pk_static_params['vfsr'] / (2**pk_static_params['precision'])
		pk_static_params['vtest_vec'] = np.arange(0.5, 1.3, 3e-3)

		print("Starting peak detector test...")
		vtest_real_dict, vtest_vout_dict = testing.test_pk_static(**pk_static_params)
		print("Ending peak detector test...")
		file_out = f'../../data/testing/{timestamp_str}_pk_{pk_static_params["num_iterations"]}x.yaml'

		vtest_ideal_vec, vtest_real_vec = plotting.dict_format(vtest_real_dict)
		vout_vec = [vtest_vout_dict[vtest_ideal] for vtest_ideal in vtest_ideal_vec]
		
		# Restructuring the dictionary
		data_dict = dict(ideal=[float(v) for v in vtest_ideal_vec], 
						real=vtest_real_vec,
						output=vout_vec)
		with open(file_out, 'w') as outfile:
			yaml.dump(data_dict, outfile, default_flow_style=False)

	####################################
	### Small Chain ZCD Slow Testing ###
	####################################
	if False:
		teensy_port = 'COM5'
		
		asc_params = dict(
			# MSB -> LSB
			preamp_res 		= [0, 0],
			delay_res 		= [0, 0],
			watchdog_res 	= [0, 0, 0, 0],
			attenuator_sel	= [0, 0, 0],
			dac_sel 		= [0, 0, 0, 0, 0, 0, 0, 0],
			az_main_gain 	= [0, 0, 0],
			az_aux_gain 	= [0, 0, 0],
			oneshot_res 	= [0, 0],
			vref_preamp 	= [0, 0, 0, 0, 0, 0, 0, 0],
			vdd_aon			= [0, 0, 0, 0, 0],
			vdd_signal		= [0, 0, 0, 0, 0],
			en_main			= [0],
			en_small		= [1])

		offset_small_params = dict(
			teensy_port=teensy_port,
			aux_port="COM3",
			num_iterations=200,
			vfsr=3.3,
			vdd=1.8,
			precision=16, 
			tref_clk=1/3.75e6)

		# Program scan
		print("Constructing scan chain...")
		asc = scan.construct_ASC(**asc_params)
		print(f"Programming scan...{asc}")
		testing.test_program_scan(com_port=teensy_port, ASC=asc)

		# Run the test
		vlsb = offset_small_params['vfsr'] / (2**offset_small_params['precision'])
		vincm_vec = np.arange(0.5, 0.9, 50e-3)
		vdiff_vec = np.arange(-0.2, 0.2, 5e-3)
		offset_small_params['vtest_dict'] = {float(vincm):list(vdiff_vec) for vincm in vincm_vec}

		file_out = f'../../data/testing/{timestamp_str}_zcdSmallOffset_{offset_small_params["num_iterations"]}x.yaml'

		overflow_dict = testing.test_offset_small(**offset_small_params)

		with open(file_out, 'w') as outfile:
			yaml.dump(overflow_dict, outfile, default_flow_style=False)

	################################
	### Small Chain Fast Testing ###
	################################
	if False:
		f_atten = -20 # dB; CHANGE THIS WITH HARDWARE

		asc_params = dict(
			# MSB -> LSB TODO check that autozero gain...
			preamp_res 		= [0, 0],
			delay_res 		= [0, 0],
			watchdog_res 	= [0, 0, 0, 0],
			attenuator_sel	= [0, 0, 0],
			dac_sel 		= [1, 1, 1, 1, 1, 1, 1, 1],
			az_main_gain 	= [0]*3,
			az_aux_gain 	= [0]*3,
			oneshot_res 	= [0, 0],
			vref_preamp 	= [0, 0, 0, 0, 0, 0, 0, 0], # TODO measure this bad boy
			vdd_aon			= [0, 0, 0, 0, 0],
			vdd_signal		= [0, 0, 0, 0, 0],
			en_main			= [0],
			en_small		= [1])

		vin_amp_vec = np.arange(0.7, 1.3, 100e-3)
		# vin_amp_vec = 
		test_tdiff_small_params = dict(
			teensy_port='COM5',
			num_iterations=100,
			asc_params=asc_params,
			ip_addr='192.168.1.4',
			gpib_addr=15,
			vin_bias=0.23,
			tref_clk=1/3.75e6)

		for vin_amp in vin_amp_vec:
			timestamp = datetime.now()
			timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")

			file_constr_lst = [timestamp_str,
				f'vin{round(vin_amp, 2)}V',
				f'{test_tdiff_small_params["num_iterations"]}x',
				f'vb{test_tdiff_small_params["vin_bias"]}V']
			
			file_out = f'../../data/testing/{"_".join(file_constr_lst)}.yaml'
			test_tdiff_small_params['vin_amp'] = float(vin_amp)
			tdiff_vec = testing.test_tdiff_small(**test_tdiff_small_params)
			tdiff_vec = [float(tdiff) for tdiff in tdiff_vec]

			dump_data = dict(config=test_tdiff_small_params,
				f_atten=f_atten,
				data=tdiff_vec)
			with open(file_out, 'w') as outfile:
				yaml.dump(dump_data, outfile, default_flow_style=False)


	###############################
	### VREF_ATTEN Code-Getting ###
	###############################
	if False:
		asc_params = dict(
			# MSB -> LSB TODO check that autozero gain...
			preamp_res 		= [0, 0],
			delay_res 		= [0, 0],
			watchdog_res 	= [0, 0, 0, 0],
			attenuator_sel	= [0, 0, 0],
			dac_sel 		= [0, 0, 1, 1, 1, 1, 1, 1],
			az_main_gain 	= [0]*3,
			az_aux_gain 	= [0]*3,
			oneshot_res 	= [0, 0],
			vref_preamp 	= [0, 1, 1, 1, 1, 1, 1, 1],
			vdd_aon			= [0, 0, 0, 0, 0],
			vdd_signal		= [0, 0, 0, 0, 0],
			en_main			= [0],
			en_small		= [0])

		get_vref_target_params = dict(
			com_port='COM5',
			num_iterations=100,
			vfsr=3.3,
			precision=16)

		# Program scan
		print("Constructing scan chain...")
		asc = scan.construct_ASC(**asc_params)
		print(f"Programming scan...{asc}")
		testing.test_program_scan(com_port=get_vref_target_params['com_port'], ASC=asc)

		# Find the target voltage
		vref_target, code = testing.get_vref_atten_target(**get_vref_target_params)

		# Determine what code on the Teensy matches
		code_binary = [int(i) for i in list('{0:0b}'.format(code))] # MSB->LSB
		extra_zeros = [0]*(get_vref_target_params['precision']-len(code_binary)) # Zero padding as needed
		code_binary = extra_zeros + code_binary
		code_str = ''.join([str(c) for c in code_binary])
		print(f'Target: {vref_target} V -> {code_binary}')

		# Have the Teensy match
		teensy_ser = serial.Serial(port=get_vref_target_params['com_port'],
                    baudrate=19200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=1)

		# teensy_ser.write(b'attenwrite\n')
		# for b in code_binary:
		# 	teensy_ser.write(code_str.encode())
		# print(teensy_ser.readline())

	#######################################
	### One-Shot Pulse Detector Outputs ###
	#######################################
	if False:
		asc_params = dict(
			# MSB -> LSB
			preamp_res 		= [0, 0],
			delay_res 		= [1]*2, # [0, 0],
			watchdog_res 	= [1]*4, # [0, 0, 0, 0],
			attenuator_sel	= [1, 0, 0],
			dac_sel 		= [1, 0, 0, 0, 0, 0, 1, 1], # [1] + [0]*7,
			az_main_gain 	= [1]*3,
			az_aux_gain 	= [1]*3,
			# oneshot_res 	= [0, 0],
			vref_preamp 	= [0, 1, 1, 1, 1, 1, 1, 1],
			vdd_aon			= [0, 0, 0, 0, 0],
			vdd_signal		= [0, 0, 0, 0, 0],
			en_main			= [0],
			en_small		= [0])

		scratch_oneshot_params = dict(
			teensy_port='COM5',
			num_iterations=10000,
			# asc_params=asc_params,
			ip_addr='192.168.1.108',
			gpib_addr=15,
			vin_bias=0.23,
			tref_clk=1/3.75e6,
			vin_amp=1.1)

		oneshot_res_vec = [[1,1]]
		# oneshot_res_vec = [[a,b] for a in range(2) for b in range(2)]
		for oneshot_res in oneshot_res_vec:
			asc_params['oneshot_res'] = oneshot_res
			scratch_oneshot_params['asc_params'] = asc_params

			misc = input(f'Oneshot Setting: {oneshot_res}. Run? (y/n)').lower()
			if misc == 'y':
				tdiff_vec = testing.test_tdiff_small(**scratch_oneshot_params)
				# tdiff_vec = [float(tdiff) for tdiff in tdiff_vec]


	###############################
	### Main Chain Fast Testing ###
	###############################
	if True:
		asc_params = dict(
			# MSB -> LSB
			preamp_res 		= [0, 0],
			delay_res 		= [0]*2, # [0, 0],
			watchdog_res 	= [0]*4, # [0, 0, 0, 0],
			attenuator_sel	= [1, 0, 0],
			dac_sel 		= [0, 1, 1, 1, 1, 1, 1, 0], # [1] + [0]*7,
			az_main_gain 	= [1]*3,
			az_aux_gain 	= [1]*3,
			oneshot_res 	= [0, 0],
			vref_preamp 	= [0, 1, 1, 1, 1, 1, 1, 1],
			vdd_aon			= [0, 0, 0, 0, 0],
			vdd_signal		= [0, 0, 0, 0, 0],
			en_main			= [0],
			en_small		= [0])

		test_tdiff_main_params = dict(
			teensy_port='COM5',
			num_iterations=10000,
			asc_params=asc_params,
			ip_addr='192.168.1.108',
			gpib_addr=15,
			tref_clk=1/3.75e6)

		vin_bias_vec = [0]

		# vin_amp_vec = np.arange(1.0, 2.0, 100e-3)
		# vin_amp_vec = np.arange(0.5, 0.8, 100e-3)
		# vin_amp_vec = np.arange(0.8, 0.1, -0.1)
		vin_amp_vec = [0.8]

		for vin_bias in vin_bias_vec:
			for vin_amp in vin_amp_vec:
				test_tdiff_main_params['vin_amp'] = float(vin_amp)
				test_tdiff_main_params['vin_bias'] = float(vin_bias)

				timestamp = datetime.now()
				timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")

				file_constr_lst = [timestamp_str,
					f'vin{round(vin_amp, 2)}V',
					f'{test_tdiff_main_params["num_iterations"]}x',
					f'vb{test_tdiff_main_params["vin_bias"]}V',
					'main']
				
				file_out = f'../../data/testing/{"_".join(file_constr_lst)}.yaml'
				tdiff_vec = testing.test_tdiff_main(**test_tdiff_main_params)
				tdiff_vec = [float(tdiff) for tdiff in tdiff_vec]

				dump_data = dict(config=test_tdiff_main_params,
					data=tdiff_vec,
					notes="")
				with open(file_out, 'w') as outfile:
					yaml.dump(dump_data, outfile, default_flow_style=False)

	###########################################
	### Board-Level Jitter from Small Chain ###
	###########################################
	if False:
		test_fflvl_jitter_params = dict(
			teensy_port='COM3',
			num_iterations=10000,
			twait=250e-9,
			ip_addr='192.168.1.4',
			gpib_addr=15,
			tref_clk=1/3.75e6)
 
		file_out = f'../../data/testing/{timestamp_str}_{test_fflvl_jitter_params["num_iterations"]}x_boardJitter.yaml'
		tdiff_vec = testing.test_fflvl_jitter(**test_fflvl_jitter_params)
		tdiff_vec = [float(tdiff) for tdiff in tdiff_vec]

		dump_data = dict(config=test_fflvl_jitter_params,
			data=tdiff_vec)
		with open(file_out, 'w') as outfile:
			yaml.dump(dump_data, outfile, default_flow_style=False)

	##############################################
	### Scratch: Check Biasing of On-Board OTA ###
	##############################################
	if False:
		rm = pyvisa.ResourceManager()
		dg535 = DG535(rm)
		dg535.open_prologix(ip_addr='192.168.1.108', gpib_addr=15)

		# Sanity checking DG535 status
		dg535.write("CL")
		print(f"Error Status: {dg535.query('ES')}")
		print(f"Instrument Status: {dg535.query('IS')}")

		cmd_lst = [
			"TM 1",						# External trigger
			"TS 1",						# Rising edge trigger
			"TL 1.00",					# Edge trigger level
			"TZ 0,1",					# Trigger is high impedance
			"TZ 1,0",					# T0 termination 50Ohm
			"OM 1,3",					# T0 output VARiable
			# f"OO 1,0.8",				# T0 channel offset
		]

		for cmd in cmd_lst:
			dg535.write(cmd)

		cont = True
		while cont:
			vin_bias_str = input('Bias voltage: ')
			try:
				vin_bias = float(vin_bias_str)
				dg535.write(f'OO 1,{vin_bias}') # T0 channel offset
			except:
				print(f'{vin_bias_str} not a float')

			cont_prompt = input('Continue? y/n').lower()
			cont = cont_prompt == 'y'

	################################################
	### Main Chain: Detect Realistic MCP Pulses? ###
	################################################
	if False:
		asc_params = dict(
			# MSB -> LSB
			preamp_res 		= [0, 0],
			delay_res 		= [0]*2, # [0, 0],
			watchdog_res 	= [0]*4, # [0, 0, 0, 0],
			attenuator_sel	= [1, 1, 1],
			dac_sel 		= [0, 1, 1, 1, 1, 1, 1, 0],
			az_main_gain 	= [1]*3,
			az_aux_gain 	= [1]*3,
			oneshot_res 	= [0, 0],
			vref_preamp 	= [0, 1, 1, 1, 1, 1, 1, 1],
			vdd_aon			= [0, 0, 0, 0, 0],
			vdd_signal		= [0, 0, 0, 0, 0],
			en_main			= [0],
			en_small		= [0])
 
		mcp_detect_params = dict(teensy_port='COM5',
			num_iterations=10000,
			asc_params=asc_params)

		cont = True
		while cont:
			testing.sanity_mcp_pulse(**mcp_detect_params)
			cont_raw = input('Continue? y/n').lower()
			cont = cont_raw=='y'

	#########################################
	### Get the Keysight33500B to Respond ###
	#########################################
	if False:
		teensy_ser = serial.Serial(port='COM5',
            baudrate=19200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=5)

		rm = pyvisa.ResourceManager()
		arb = Keysight33500B(rm)
		arb.open_gpib()

		cmd_lst = [
			"*RST; *CLS",			# Reset device
			"OUTP1:LOAD 50",		# CH1 driving 50Ohm load
			"TRIG1:SOUR EXT",		# External trigger source
			"TRIG1:SLOP POS",		# Input trigger rising edge
			# "TRIG:LEV 1.8",		# Input and output trigger level - only 33600 can do this
			"TRIG1:DEL 1E-5",		# 1us delay between trigger and output pulse
			"OUTP:TRIG:SOUR CH1",	# Set the trigger output to channel 1
			"OUTP:TRIG:SLOP POS"	# Output pulse rising edge
			"OUTP:TRIG ON",			# Turn on rear panel external trigger
		]

		for cmd in cmd_lst:
			arb.write(cmd)

		cont = input('Continue? (y/n)').lower()
		if cont == 'y':
			while True:
				# Repeatedly send the START pulse
				print('--- Feeding START')
				teensy_ser.write(b'tdcmainstart\n')
				print(teensy_ser.readline())

				# See the oscilloscope while probing the output CH1

	################################
	### Get the DG535 to Respond ###
	################################
	if False:
		teensy_ser = serial.Serial(port='COM3',
                    baudrate=19200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=5)

		rm = pyvisa.ResourceManager()
		dg535 = DG535(rm)
		dg535.open_prologix(ip_addr='192.168.1.4', gpib_addr=15)
		cmd_lst = [
			"CL",						# Clear
			"TM 1",						# External trigger
			"TS 1",						# Rising edge trigger
			"TL 1.00",					# Edge trigger level
			"TZ 0,1",					# Trigger is high impedance
			f"DT 2,1,250e-9", 			# Set delay A=T0+twait
			"TZ 1,1",					# T0 termination HiZ
			"TZ 2,0",					# A termination 50ohm
			"OM 1,3",					# T0 output VARiable
			"OM 2,3",					# A output VARiable
			f"OA 2,1.8",				# A channel amplitude
			f"OA 1,3.3",				# T0 channel amplitude
			f"OO 2,0",					# A channel offset
			f"OO 1,0",					# T0 channel offset
		]

		for cmd in cmd_lst:
			dg535.write(cmd)

		cont = input('Continue? (y/n) ').lower()
		if cont == 'y':
			while True:
				# Repeatedly send the START pulse
				print('--- Feeding START')
				teensy_ser.write(b'tdcsmallstart\n')
				print(teensy_ser.readline())

				# See the oscilloscope while probing the output T0


	########################################
	### Scratch: Measure Long Coax Delay ###
	########################################
	'''
	The output sources solely from T0.
	T0 - splitter 
		-> long coax
		-> shorter coax
	View on oscilloscope.
	'''
	if False:
		rm = pyvisa.ResourceManager()
		dg535 = DG535(rm)
		dg535.open_prologix(ip_addr='192.168.1.4', 
			gpib_addr=15)
		
		dg535.write("CL")
		print(f"Error Status: {dg535.query('ES')}")
		print(f"Instrument Status: {dg535.query('IS')}")

		cmd_lst = [
			"TZ 0,1",					# Trigger is high impedance
			"TZ 1,0",					# T0 termination 50ohm (OPT-04B)
			"OM 1,3",					# T0 output VARiable
			f"OA 1,3.3",				# T0 channel amplitude
			f"OO,1,0",					# T0 channel offset
			"TM 0",						# Internal trigger
			"TR 0,10000",				# 10kHz trigger rate
		]

		for cmd in cmd_lst:
			dg535.write(cmd)

	########################################
	### Scratch: R/W Values from the TDC ###
	########################################
	"""
	teensy_sanity.ino
		tdc_rw_reg()
		tdc_read_reg()
		tdc_arm()
	"""
	if False:
		teensy_port = 'COM3'
		teensy_ser = serial.Serial(port=teensy_port,
			baudrate=19200,
			parity=serial.PARITY_NONE,
			stopbits=serial.STOPBITS_ONE,
			bytesize=serial.EIGHTBITS,
			timeout=5)
		for _ in range(280):
			print(teensy_ser.readline())


	################################################		
	### Scratch: Testing Teensy DAC Voltage Ramp ###
	################################################
	"""
	teensy_sanity.ino
		setup()
	"""
	if False:
		vlsb = 3.3/(2**16)
		# vdac_vec = np.arange(0.5, 1.8, vlsb*10)
		vdac_vec = np.arange(0.5, 1.8, 0.1)
		aux_ser = serial.Serial(port="COM3",
                    baudrate=19200,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS,
                    timeout=2)
		
		for vdac in vdac_vec:
			code = int(round(vdac/vlsb))
			aux_ser.write(b'peakslow\n')
			aux_ser.write(str(code).encode())
			print(f'Voltage/Code: {round(vdac, 4)}/{code}')
			print(f'Ramping to code {aux_ser.readline()}')
			time.sleep(1)

	#########################################
	### Small Chain ZCD Comparator Offset ###
	#########################################
	if False:
		vincm_vec = np.arange(0.6, 0.9, 50e-3)
		vdiff_vec = np.arange(-0.1, 0.1, 5e-3)
		vtest_dict = {vincm:vdiff_vec for vincm in vincm_vec}

		offset_zcd_params = dict(
			teensy_port="COM3",
			aux_port="COM4",
			num_iterations=100,
			vtest_dict=vtest_dict,
			vfsr=3.3,
			precision=16,
			tref_clk=1/16e6)
		
		file_out = f'../../data/testing/{timestemp_str}_zcdsmall_{offset_zcd_params["num_iterations"]}x.yaml'

		high_rate_dict = testing.test_offset_zcd_static(**offset_zcd_params)

		# Restructuring some of the data to get vincm:dict(vdiff=[vdiff values],
		# 											high_rate=[high_rate values])
		restruct_dict = dict()
		for vin_pair, high_rate in high_rate_dict.items():
			vincm = vin_pair[0]
			vdiff = vin_pair[1]
			if vincm not in restruct_dict.keys():
				restruct_dict[vincm] = dict(vdiff=[vdiff],
											high_rate=[high_rate])
			else:
				restruct_dict[vincm]['vdiff'].append(vdiff)
				restruct_dict[vincm]['high_rate'].append(high_rate)

		# Dump into a yaml file because screw CSVs
		with open(file_out, 'w') as outfile:
			yaml.dump(restruct_dict, outfile, default_flow_style=False)

		# for vincm, vals in restruct_dict.keys():
		# 	vdiff_vec = vals['vdiff']
		# 	high_rate_vec = vals['high_rate']

		# 	# Plot for visibility
		# 	plt.figure()
		# 	plt.plot(vdiff_vec, high_rate_vec)
		# 	plt.xlabel('Differential Input Voltage')
		# 	plt.ylabel('Noise Event Rate (event/s)')
		# 	plt.grid(True)
		# 	plt.show()


	###############
	### Scratch ###
	###############
	if False:
		rm = pyvisa.ResourceManager()
		keithley = gpib.rsrc_open(rm)
		gpib.voltmeter_Keithley2634B_config(sm=keithley,
			smu=testing.SMU_A, autorange=True, vrange=1.8)
		keithley.write(f'print(smu{testing.SMU_A}.measure.v())')
		vout_str = keithley.read()
		print(f'vout_str: {vout_str}')
		print(float(vout_str))
		keithley.close()

if __name__ == "__main__":
	try:
		run_main()
	except:
		extype, value, tb = sys.exc_info()
		traceback.print_exc()
		pdb.post_mortem(tb)