import pyvisa, serial
from warnings import warn

class LabInstrument(object):
	'''
	General lab instrument. Intended as a superclass for devices which are meant
	to be programmatically controlled through GPIB.

	This could technically be reworked for devices controlled over RS-232 as well, 
	but it would be a lot of rewriting functions.
	'''
	def __init__(self, rm):
		self.rm = rm
		self.rsrc = None
		self.is_open = False

		is_correct = False
		while not is_correct:
			# List resources for user selection by index
			num_rsrc = len(self.rm.list_resources())
			print('Index: Resource ID')
			for i, x in enumerate(self.rm.list_resources()):
				print(f'{i}: {x}')

			while True:
				idx_str = input('Choose Device Index: ')
				try:
					rsrc = self.rm.open_resource(self.rm.list_resources()[int(idx_str)])
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
			else:
				self.rsrc = rsrc
				self.is_open = True

	def get_rsrc(self):
		return self.rsrc

	def get_rm(self):
		return self.rm

	def write(self, msg):
		if self.is_open:
			self.rsrc.write(msg)
		else:
			warn('Attempting to write to a closed resource')

	def close(self):
		if self.is_open:
			if self.rsrc != None:
				self.rsrc.close()
			self.is_open = False
		else:
			warn(f'Resource {self.rsrc} not open')

	def __str__(self):
		return f"{type(self).__name__} : {self.rsrc}"


class KeysightE3631A(LabInstrument):
	def __init__(self, rm):
		super().__init__(rm)
		self.rsrc.write('DISP ON') 		# Enable the display
		self.rsrc.write(f'OUTP OFF') 	# Turn off all outputs to start

	def close(self):
		self.rsrc.write(f'OUTP OFF')	# Turn off all outputs
		super().close()

class Keysight33500B(LabInstrument):
	def __init__(self, rm):
		super().__init__(rm)
		# Ensure outputs are off to begin
		self.rsrc.write("OUTPUT1 OFF")
		self.rsrc.write("OUTPUT2 OFF")

	def close(self):
		# Turn off outputs
		self.rsrc.write("OUTPUT1 OFF")
		self.rsrc.write("OUTPUT2 OFF")
		super().close()


class DG535(LabInstrument):
	def __init__(self, rm, gpib_addr):
		super().__init__(rm)
		# Prologix commands
		self.rsrc.write("++mode 1")				# Prologix control
		self.rsrc.write_termination = '\r\n'
		self.rsrc.read_termination = '\r\n'
		self.rsrc.write(f"++addr {gpib_addr}") 	# GPIB address
		self.rsrc.write("++auto 1") 			# Automatic read after write for query
		self.rsrc.write("++read_tmo_ms 500") 	# Extend read timeout time
		self.rsrc.write("++eos 3") 				# No additional termination character
		self.rsrc.write("++eoi 1") 				# Assert EOI after last byte
		self.rsrc.write("++eot_enable 0") 		# No EOT character on EOI

		# Querying DG535 status
		self.rsrc.write("CL") # Clear DG535
		print(f"Instrument Status:\t{self.rsrc.query('IS')}")
		print(f"Error Status:\t{self.rsrc.query('ES')}")

		# DG535 initialization
		cmd_vec = [
			"DT 2,1,0",		# Delay A=T+1 (default 800ns pulse)
			"TZ 2,0",		# 50Ohm output termination for OPT-04B BNC falltime modifier
			"OM 2,3",		# Variable output
			"OA 2,-2",		# Output amplitude -2V
			"OO 2,1.3",		# Output offset +1.3V
			"TM 0",			# Trigger mode: internal
			"TR 0,10000",	# Internal trigger: 10kHz
		]
		for cmd in cmd_vec:
			self.rsrc.write(cmd)

	def close(self):
		# Clear instrument
		self.rsrc.write('CL')

		super().close()

# def voltmeter_Keithley2634B_config(sm, smu=SMU_A, autorange=True,
# 	vrange=1.8):
# 	'''
# 	Configures the Keithley2634B as a measurement-only voltmeter, i.e. it turns
# 		off the source in the channel.
# 	Inputs:
# 		sm: Visa Resource object. The device with an opened connection.
# 		smu: SMU_A or SMU_B (above). Chooses between channels A and B.
# 		autorange: Boolean. True to have the device autorange the voltage
# 			measurement.
# 		vrange: Optional float. The voltage measure range.
# 	Returns:
# 		None.
# 	'''
# 	smu_str = f'smu{smu}'

# 	# Turn off the source for that connection on the Keithley
# 	sm.write(f'{smu_str}.source.output = {smu_str}.OUTPUT_OFF')

# 	# Set the voltage measurement range
# 	autorange_str = 'OFF' if not autorange else 'ON'
# 	sm.write(f'{smu_str}.measure.autorangev = {smu_str}.AUTORANGE_{autorange_str}')
# 	if not autorange:
# 		sm.write(f'{smu_str}.measure.rangev = {vrange}')

# 	return

if __name__ == "__main__":
	is_correct = False
	rm = pyvisa.ResourceManager()
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

	# If not correct, close the connection
	if not is_correct:
		rsrc.close()