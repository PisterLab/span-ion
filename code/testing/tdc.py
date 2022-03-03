# This is code intended for using the TI TDC7200. Device documentation can be 
# found here: 
# https://www.ti.com/lit/ds/symlink/tdc7200.pdf

from warnings import warn
from pprint import pprint

# Register reset values (hex) -> int(hex_str, 16)
reg_rst_map = dict(
	CONFIG1					= '00',
	CONFIG2 				= '40',
	INT_STATUS 				= '00',
	INT_MASK				= '07',
	COARSE_CNTR_OVF_H 		= 'FF',
	COARSE_CNTR_OVF_L 		= 'FF',
	CLOCK_CNTR_OVF_H 		= 'FF',
	CLOCK_CNTR_OVF_L		= 'FF',
	CLOCK_CNTR_STOP_MASK_H 	= '00',
	CLOCK_CNTR_STOP_MASK_L 	= '00',
	TIME1					= '00_0000',
	CLOCK_COUNT1 			= '00_0000',
	TIME2 					= '00_0000',
	CLOCK_COUNT2 			= '00_0000',
	TIME3 					= '00_0000',
	CLOCK_COUNT3			= '00_0000',
	TIME4 					= '00_0000',
	CLOCK_COUNT4 			= '00_0000',
	TIME5 					= '00_0000',
	CLOCK_COUNT5 			= '00_0000',
	TIME6 					= '00_0000',
	CALIBRATION1 			= '00_0000',
	CALIBRATION2 			= '00_0000')

# Number of bits in a register's data
reg_size_map = dict(
	CONFIG1					= 8,
	CONFIG2 				= 8,
	INT_STATUS 				= 8,
	INT_MASK				= 8,
	COARSE_CNTR_OVF_H 		= 8,
	COARSE_CNTR_OVF_L 		= 8,
	CLOCK_CNTR_OVF_H 		= 8,
	CLOCK_CNTR_OVF_L		= 8,
	CLOCK_CNTR_STOP_MASK_H 	= 8,
	CLOCK_CNTR_STOP_MASK_L 	= 8,
	TIME1					= 24,
	CLOCK_COUNT1 			= 24,
	TIME2 					= 24,
	CLOCK_COUNT2 			= 24,
	TIME3 					= 24,
	CLOCK_COUNT3			= 24,
	TIME4 					= 24,
	CLOCK_COUNT4 			= 24,
	TIME5 					= 24,
	CLOCK_COUNT5 			= 24,
	TIME6 					= 24,
	CALIBRATION1 			= 24,
	CALIBRATION2 			= 24)

# Register addresses (hex) -> int(hex_str, 16)
reg_addr_map = dict(
	CONFIG1					= '0x00',
	CONFIG2 				= '0x01',
	INT_STATUS 				= '0x02',
	INT_MASK				= '0x03',
	COARSE_CNTR_OVF_H 		= '0x04',
	COARSE_CNTR_OVF_L 		= '0x05',
	CLOCK_CNTR_OVF_H 		= '0x05',
	CLOCK_CNTR_OVF_L		= '0x07',
	CLOCK_CNTR_STOP_MASK_H 	= '0x08',
	CLOCK_CNTR_STOP_MASK_L 	= '0x09',
	TIME1					= '0x10',
	CLOCK_COUNT1 			= '0x11',
	TIME2 					= '0x12',
	CLOCK_COUNT2 			= '0x13',
	TIME3 					= '0x14',
	CLOCK_COUNT3			= '0x15',
	TIME4 					= '0x16',
	CLOCK_COUNT4 			= '0x17',
	TIME5 					= '0x18',
	CLOCK_COUNT5 			= '0x19',
	TIME6 					= '0x1A',
	CALIBRATION1 			= '0x1B',
	CALIBRATION2 			= '0x1C')

# Number of calibration periods for CALIBRATION2_PERIODS code 
code_cal2_map = {0 : 2,
				 1 : 10,
				 2 : 20,
				 3 : 40}

# Number of timers used for NUM_STOPS code
code_numstop_map = {0: 1,
					1: 2,
					2: 3,
					3: 4,
					4: 5,
					5: 1,
					6: 1,
					7: 1}

addr_reg_map = {val:key for key,val in reg_addr_map.items()}

def construct_wdata1(force_cal=1, parity_en=1, trigg_edge=0, stop_edge=0, 
	start_edge=0, meas_mode=1, start_meas=1) -> int:
	'''
	Inputs:
		force_cal: 0 to not perform calibration after interrupted measurement.
			1 to perform calibration at the end.
		parity_en: 1 to enable parity bit for measurement result registers
			(even parity).
		trigg_edge: 0 = TRIGG output is a rising edge, 1 = falling edge. 
		stop_edge: 0 = STOP event is a rising edge, 1 = falling edge.
		start_edge:	0 = START event is a rising edge, 1 = falling edge.
		meas_mode: 0 = Measurement Mode 1 for expected ToF <500ns,
			1 = Measurement Mode 2. 3 and 4 reserved for te future.
		start_meas: 0 = no effect. 1 = start a new measurement and clear all 
			the bits in the interrupt status register and start measurement. 
			Resets the content of all measurement result registers.
	Returns:
		Integer < 2^8 with 8 bits of write data for Configuration Register
		1 in the TDC7200.
	Raises:
		AssertionError if any of the input values are invalid.
	'''
	# Sanity checking values
	assert start_meas in (0,1), f"START_MEAS {start_meas} must be 0 or 1"
	assert meas_mode in range(4), f"MEAS_MODE {meas_mode} must be 0 through 3"
	assert start_edge in (0,1), f"START_EDGE {start_edge} must be 0 or 1"
	assert stop_edge in (0,1), f"STOP_EDGE {stop_edge} must be 0 or 1"
	assert trigg_edge in (0,1), f"TRIGG_EDGE {trigg_edge} must be 0 or 1"
	assert parity_en in (0,1), f"PARITY_EN {parity_en} must be 0 or 1"
	assert force_cal in (0,1), f"FORCE_CAL {force_cal} must be 0 or 1"

	return (force_cal << 7) + (parity_en << 6) + \
		(trigg_edge << 5) + (stop_edge << 4) + \
		(meas_mode << 1) + start_meas

def construct_wdata2(calibration2_periods, avg_cycles, num_stop) -> int:
	'''
	Inputs:
		calibration2_periods: Integer<4. 0 = 2 clock periods, 1 = 10 clock 
			periods, 2 = 20 clock periods, 3 = 40 clock periods.
		avg_cycles: Integer<8. 2^(avg_cycles) measurement cycles for averaging.
		num_stop: Integer<8. 0-4 = 1-5 stops. 5-7 = no effect. Single stop.
	Returns:
		Integer < 2^8 with 8 bits of write data for Configuration Register
		2 in the TDC7200.
	Raises:
		AssertionError if any of the input values are invalid.
	'''
	# Sanity checking values
	assert calibration2_periods in range(4), f"CALIBRATION2_PERIODS \
		{calibration2_periods} must be 0 through 3."
	assert avg_cycles in range(8), f"AVG_CYCLES {avg_cycles} must be 0 through \
		7."
	assert num_stop in range(8), f"NUM_STOP {num_stop} must be 0 through 7."

	return (num_stop) + (avg_cycles << 3) + (calibration2_periods >> 6)

def construct_config(is_read=True, addr=0, wdata=0) -> int:
	'''
	Inputs:
		is_read: Boolean. True to read, False to write.
		addr: Integer. Register address (in decimal).
		wdata: Integer<256. Data to write into the register in question.
			Only used if is_read is False.
	Returns:
		Two integers. Going MSB->LSB:
		int_command:
			1b auto-increment 
			1b read/write
			6b address
		int_wdata:
			8b write data (if relevant, otherwise all 1)
	Raises:
		Warning if the write data is greater than the max value. If this is 
			the case, the write data will be truncated to the 8 least 
			significant bits.
		Relevant documentation: 
			https://www.ti.com/lit/ds/symlink/tdc7200.pdf
			Figure 21
	'''
	# Warn the user about truncating write data if necessary
	if wdata >= (1<<8):
		warn(f'Write data {wdata} exceeds max value {(1<<8)-1}. \
			Data will truncate to {wdata & ((1<<9)-1)}')
		wdata = wdata & ((1<<9)-1)
	
	# Construct the command field
	bit_rw = 0 if is_read else 1
	bit_incr = 0
	int_command = addr + (bit_rw << 6) + (bit_incr << 7)

	# Construct the data field; note this may not be used
	int_wdata = (1<<9)-1 if is_read else wdata

	return int_command, int_wdata

def get_addr(int_command):
	'''
	Inputs:
		int_command: Integer < 2^8. Going MSB->LSB:
			1b auto-increment 
			1b read/write
			6b address
	Returns:
		hex_addr: Hex string 0x## of the address.
	'''
	int_addr = int_command % (1<<6)
	return hex(int_addr)

def config_tdc(teensy_ser, int_command, int_wdata, is_read=False):
	'''
	Inputs:
		teensy_ser:
		int_command: Integer < 2^8. Going MSB->LSB:
			1b auto-increment 
			1b read/write
			6b address
		int_wdata: Integer < 2^8. Going MSB->LSB:
			8b write data (if relevant)
	Returns:
		Read data, if applicable.
	Notes:
	'''
	rdata = None
	
	# Send command byte
	teensy_ser.write(int_command.to_bytes(1, 'big'))

	# Send write data info or receive read data byte
	addr = get_addr(int_command)
	if not is_read:
		teensy_ser.write(int_wdata.to_bytes(1, 'big'))
	else:
		# TODO get read data from Teensy
		rdata = teensy_ser.readline()

	return rdata

def calc_tof(cal1, cal2, cal2_periods, time_1, time_x, count_n, tper, mode=2):
	'''
	Inputs:
		cal1: Integer. CALIBRATION1 register value. TDC count for first
			calibration cycle.
		cal2: Integer. CALIBRATION2 register value. TDC count for second
			calibration cycle.
		cal2_periods: CALIBRATION2_PERIODS value in register CONFIG2.
		time_1:	Time 1 measurement given by the TIME1 register.
		time_x: Time n or n+1 for modes 1 and 2, respectively.
		count_n: Value of nth clock count, i.e. registers CLOCK_COUNTn.
			Only used for mode 2.
		tper: External clock period (s).
		mode: 1 or 2 for measurement modes 1 and 2, per documentation (see
			see notes).
	Returns:
		Returns the time of flight between the START to the nth STOP in seconds.
	Notes:
		Implements the ToF calculation for the TI TDC7200
		(https://www.ti.com/lit/ds/symlink/tdc7200.pdf). See sections
		"Calculating Time-of-Flight"
	'''
	cal_count = (cal2 - cal1)/(cal2_periods-1)
	norm_lsb = tper/cal_count
	if mode == 1:
		return time_x * norm_lsb
	elif mode == 2:
		return norm_lsb * (time_1 - time_x) + (count_n * tper)
	else:
		raise ValueError(f'Measurement mode {mode} must be 1 or 2')

if __name__ == '__main__':
	wdata1 = construct_wdata1(force_cal=1,
		parity_en=0,
		trigg_edge=0,
		stop_edge=1,
		start_edge=0,
		meas_mode=1,
		start_meas=1)

	print("{0:b}".format(wdata1))