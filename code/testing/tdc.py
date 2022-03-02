from warnings import warn

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

addr_reg_map = {val:key for key,val in reg_addr_map.items()}

def construct_config(is_read=True, addr=0, wdata=0):
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
			8b or 24b write data (if relevant, otherwise all 1)
	Raises:
		Warning if the write data is greater than the max value. If this is 
			the case, the write data will be truncated to the 8 least 
			significant bits.
		Relevant documentation: 
			https://www.ti.com/lit/ds/symlink/tdc7200.pdf
			Figure 21
	'''
	max_wdata_val = 
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