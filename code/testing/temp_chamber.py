import minimalmodbus, serial

def read_temp(instr, precision):
	"""
	Inputs:
		instr: minimalmodbus Instrument. 
		precision: Integer. Number of decimal points in the final readout.
	Returns: 
		Name: Float. The internal temperature (in Celsius?) of the temperature
		chamber.
	Notes:
	"""
	readout_int = instr.read_register(100, precision)
	return readout_int / 10**precision

def get_static_temp(instr, precision):
	"""
	Inputs:
		instr: minimalmodbus Instrument. 
		precision: Integer. Number of decimal points in the final readout.
	Returns:
	Notes:
	"""
	readout_int = instr.read_register(4122, precision)
	return readout_int / 10**precision