import visa

def test_peak(arb_name, output_num):
	'''
	Inputs:
		arb_name: String. Name to use in the connection for the waveform 
			generator, e.g. "USB0::0x0957::0x2C07::MY57801384::0::INSTR"
		output_num: Integer; likely 1 or 2. The output source used for testing
			for waveform generators with multiple output sources. 
	Returns:

	'''
	# Interface with waveform generator
	rm = visa.ResourceManager()
	arb = rm.open_resource(arb_name)

	# Sanity checking that it's the correct device
	arb.query("*IDN?")

	# Zin setting expected by arb is capacitive
	arb.write(f"OUTPUT{output_num}:LOAD INF")
	arb.write(f"SOURCE{output_num}:FUNCTION DC") # TODO change

	# Setting the waveform generator to 0 initially to avoid breaking things
	arb.write(f"SOURCE{output_num}:VOLTAGE:OFFSET 0")

	# TODO: generate pulse with as-of-yet unknown parameters
	# TODO: run pulse
	# TODO: measure peak value
	# TODO: compare the expected vs. measured peak value

	# TODO: wait

	# TODO: reset peak detector
	pass