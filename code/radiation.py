import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
from scipy import interpolate
import random
import pandas as pd
import warnings

h_eV 		= 4.136e-15 		# eV*s, Planck's constant
h_J 		= 6.626e-34 		# J*s, Planck's constant
c 			= 3e8 				# m/s, speed of light
m0 			= 9.10938356e-31 	# kg, electron mass
lambda_c 	= h_J / (m0*c) 		# m, Compton wavelength
q 			= 1.602e-19 		# C, electron charge

def scatter_compton(lambda_i, theta_scatter, E_ion):
	'''
	Inputs:
		lambda_i: Float. Incoming photon wavelength in meters.
		theta_scatter: Float. Scattering angle in radians.
		E_ion: Float. Energy in eV to generate a single
			electron-hole pair in the substrate.
	Outputs:
		lambda_f: Float. Resulting photon wavelength in meters.
		num_ehp: Number of generated electron-hole pairs.
	'''
	# Energy of incoming photon (eV)
	E_i = get_E(lambda_i)
	
	# Calculate wavelength (m) and energy (eV) of scattered result
	lambda_f = lambda_i + lambda_c * (1-np.cos(theta_scatter))
	E_f = h_eV * c / lambda_f

	E_diff = E_i - E_f
	num_ehp = E_diff / E_ion

	return lambda_f, num_ehp


def get_E(lamb):
	'''
	Inputs:
		lamb: Wavelength in meters.
	Outputs:
		Energy in eV
	'''
	return h_eV * c / lamb


def get_lambda(E):
	'''
	Inputs:
		E: Energy in eV
	Outputs:
		Wavelength in meters.
	'''
	return h_eV * c / E