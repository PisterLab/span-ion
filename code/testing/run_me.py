import serial, pyvisa, minimalmodbus
import numpy as np
import random
from datetime import date, datetime
import os, sys, time, pdb, traceback
import csv, yaml

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
			en_main			= [1],
			en_small		= [1])

		print("Constructing scan chain...")
		asc = scan.construct_ASC(**asc_params)
		# asc = [1, 1] * 22
		print(f"Programming scan...{asc}")
		scan.test_program_scan(com_port=teensy_port, ASC=asc)

	############
	### DACs ###
	############
	if False:
		which_dac = spani_globals.OUT_REF_PREAMP
		test_dac_params = dict(
			com_port='COM5',
			num_iterations=1000,
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
		pk_static_params = dict(teensy_port="COM4",
			aux_port="COM3",
			num_iterations=1,
			vfsr=3.3,
			precision=16,
			t_wait=0.001)
		pk_static_params['vtest_vec'] = np.linspace(0, 
			pk_static_params['vfsr'], 
			2**pk_static_params['precision']+1)

		vtest_real_dict, vtest_vout_dict = testing.test_pk_static(**pk_static_params)
		file_out = f'../../data/testing/{timestamp_str}_pk_{pk_static_params["num_iterations"]}x.csv'

		vtest_ideal_vec, vtest_real_vec = dict_format(vtest_real_dict)
		vout_vec = [vtest_vout_dict[vtest_ideal] for vtest_ideal in vtest_ideal_vec]

		with open(file_out, 'w', newline='') as csvfile:
			fwriter = csv.writer(csvfile, delimiter=',',
				quotechar="|", quoting=csv.QUOTE_MINIMAL)
			fwriter.writerow(['Ideal Input'] + list(vtest_real_vec))
			fwriter.writerow(['Practical Input'] + list(vtest_real_vec))
			fwriter.writerow(['Output'] + vout_vec)

	#########################################
	### Small Chain ZCD Comparator Offset ###
	#########################################
	if True:


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
			yaml.dump(erstruct_dict, outfile, default_flow_style=False)

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