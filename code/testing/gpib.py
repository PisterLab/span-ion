import pyvisa
import serial

Z_INF = 'INF'
Z_FIFTY = '50OHM'

SMU_A = 'a'
SMU_B = 'b'

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
		num_rsrc = len(rm.list_resources())
		print('Index: Resource ID')
		for i, x in enumerate(rm.list_resources()):
			print(f'{i}: {x}')

		while True:
			idx_str = input('Choose Device Index: ')
			try:
				rsrc = rm.open_resource(rm.list_resources()[int(idx_str)])
				break
			except Exception as e:
				print(e)


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

# def sourcemeter_Keithley2634B_config(sm, smu=SMU_A,
# 	inout=IO_IN, src_type=SRC_V, autorange=True, measrange=0):
# 	'''
# 	Inputs:
# 		sm: Visa Resource object. The device with an opened connection.
# 		smu: 'a' or 'b' for this device. Which SMU port to configure.
# 		inout: IO_IN or IO_OUT (see above). IO_IN/OUT indicate the sourcemeter
# 			is for measurement/source, respectively.
# 		src_type: 
# 	'''
# 	smu_str = f'smu{smu}'

# 	sm.write(f'{smu_str}.')
# 	return

def voltmeter_Keithley2634B_config(sm, smu=SMU_A, autorange=True,
	vrange=1.8):
	'''
	Configures the Keithley2634B as a measurement-only voltmeter, i.e. it turns
		off the source in the channel.
	Inputs:
		sm: Visa Resource object. The device with an opened connection.
		smu: SMU_A or SMU_B (above). Chooses between channels A and B.
		autorange: Boolean. True to have the device autorange the voltage
			measurement.
		vrange: Optional float. The voltage measure range.
	Returns:
		None.
	'''
	smu_str = f'smu{smu}'

	# Turn off the source for that connection on the Keithley
	sm.write(f'{smu_str}.source.output = {smu_str}.OUTPUT_OFF')

	# Set the voltage measurement range
	autorange_str = 'OFF' if not autorange else 'ON'
	sm.write(f'{smu_str}.measure.autorangev = {smu_str}.AUTORANGE_{autorange_str}')
	if not autorange:
		sm.write(f'{smu_str}.measure.rangev = {vrange}')

	return


def multimeter_close(multimeter):
	'''
	Closes connection to digital multimeter.
	Inputs:
		multimeter: Visa Resource object. The device with an opened connection
			to be closed.
	Returns:
		None.
	Notes:
		Keysight E3631A 
	'''
	multimeter.close()
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