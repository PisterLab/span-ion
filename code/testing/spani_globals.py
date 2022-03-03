import sys, os

OUT_DAC_MAIN 	= 0
OUT_DAC_SMALL 	= 1
OUT_VDD_MAIN 	= 2
OUT_VDD_SMALL	= 3
OUT_VDD_AON 	= 4
OUT_REF_PREAMP 	= 5

N_BITS_MAP = {
	OUT_DAC_MAIN 	: 8,
	OUT_DAC_SMALL 	: 8,
	OUT_REF_PREAMP	: 8,
	OUT_VDD_MAIN 	: 5,
	OUT_VDD_SMALL 	: 5,
	OUT_VDD_AON 	: 5}

def block_print():
	sys.stdout = open(os.devnull, 'w')

def enable_print():
	sys.stdout = sys.__stdout__

def vdiff_conv(vincm, vdiff):
	'''
	Inputs:
		vincm: Float. Input common mode in volts.
		vdiff: Float. Input differential in volts.
	Returns:
		vinp: Float. Absolute positive input voltage.
		vinn: Float. Absolute negative input voltage.
	'''
	return vincm+vdiff/2, vincm-vdiff/2