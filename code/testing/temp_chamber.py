import minimalmodbus, serial

def read_temp(instr):
	"""
	Inputs:
		instr: minimalmodbus Instrument. 
	Returns: 
		Float. The internal temperature (in Celsius?) of the temperature
		chamber.
	Notes:
		Precision set to 1 to match the display; if you set it to anything else,
		all you're doing is moving the decimal point around uselessly.
	"""
	return instr.read_register(100, 1)

def get_static_temp(instr):
	"""
	Inputs:
		instr: minimalmodbus Instrument. 
		precision: Integer. Number of decimal points in the final readout.
	Returns:
		Float. The set point (in Celsius) of the temperature chamber.
	Notes:
		Precision set to 1 to match the display; if you set it to anything else,
		all you're doing is moving the decimal point around uselessly.

	"""
	return instr.read_register(4122, 1)