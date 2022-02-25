import serial, pyvisa, minimalmodbus
import random
from datetime import date, datetime
import os, sys, time, pdb, traceback
import csv

import spani_globals, scan, bandgap, testing

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
			en_main			= [0],
			en_small		= [0])

		print("Constructing scan chain...")
		asc = scan.construct_ASC(**asc_params)
		# asc = [0, 1] * 22
		print(f"Programming scan...{asc}")
		scan.program_scan(com_port=teensy_port, ASC=asc)

	#####################
	### Test DACs ###
	#####################
	if True:
		which_dac = spani_globals.OUT_DAC_MAIN
		test_dac_params = dict(
			com_port='COM5',
			num_iterations=1,
			code_vec=range(int(2**spani_globals.N_BITS_MAP[which_dac])),
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
			fwriter.writerow(['Code'])
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