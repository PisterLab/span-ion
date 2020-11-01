import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
from scipy import interpolate
import random
import pandas as pd
import warnings

def get_pulse_widths(data_dict, sig_threshold, posedge=True):
	'''
	Inputs:
		data_dict:		Key:value is time:signal value.
		sig_threshold:	Threshold for determining an edge crossing. Used for linear interpolation.
		posedge: 		Boolean. True to indicate that a rising edge is the start of a pulse.
						False indicates a pulse is active low.
	Outputs:
		Returns a list of pulse widths in the order in which they appear.
	'''
	t_vec = list(data_dict.keys())
	t_vec.sort()
	sig_vec = [data_dict[t] for t in t_vec]
	result = []

	# Finding zero crossings of down-shifted signal vector
	sig_vec_shifted = [sig_val-sig_threshold for sig_val in sig_vec]
	zcross_start_idx = np.where(np.diff(np.signbit(sig_vec_shifted)))[0]

	# Linear interpolation of times
	for zcross_idx in zcross_start_idx:
		val_start = sig_vec_shifted[zcross_idx]
		val_stop = sig_vec_shifted[zcross_idx + 1]

		frac = val_start / (val_start - val_stop)

		tedge_start = t_vec[zcross_idx]
		tedge_stop = t_vec[zcross_idx + 1]

		t_cross = tedge_start + frac * (tedge_stop - tedge_start)

		if val_start > val_stop:
			t_negedge = t_cross
			if posedge:
				result = result + [t_negedge - t_posedge]
				t_negedge = np.inf
				t_posedge = -np.inf
		elif val_start < val_stop:
			t_posedge = t_cross
			if not posedge:
				result = result + [t_posedge - t_negedge]
				t_negedge = -np.inf
				t_posedge = np.inf
		else:
			raise ValueError("(get_pulse_widths) Edge detection isn't actually an edge!")

	return result


def siggen_oneshot(thigh, td, tlow_max, tlow_min, vlow, vhigh, tstart=0, num_pulses=100):
	'''
	Inputs:
		thigh: 		Pulse width (in seconds).
		td: 		Pulse rise and fall time (in seconds).
		tlow_max: 	Maximum time between falling edge of previous pulse and rising edge of the next one.
		tlow_min: 	Minimum time between falling edge of previous pulse and rising edge of the next one.
		vlow:		Low voltage.
		vhigh: 		High voltage.
		tstart:		Time the first rising edge starts (in esconds).
		num_pulses: Number of pulses. Default 100.
	Outputs:
		Dictionary of key:value time:value.
	'''
	t_vec = [0, tstart] if tstart != 0 else [0]
	out_vec = [vlow, vlow] if tstart != 0 else [vlow]

	t_prev = tstart

	for _ in range(num_pulses):
		tlow = np.random.uniform(tlow_min, tlow_max)

		t_pulse_vec = [t_prev+td,
					   t_prev+td+thigh, 
					   t_prev+td+thigh+td,
					   t_prev+td+thigh+td+tlow]
		pulse_vec = [vhigh, vhigh, vlow, vlow]

		t_prev = t_prev+td+thigh+td+tlow

		t_vec = t_vec + t_pulse_vec
		out_vec = out_vec + pulse_vec

	return {t_vec[i]:out_vec[i] for i in range(len(t_vec))}