import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
from scipy import interpolate
import random
import pandas as pd
import warnings

'''
This file is intended as a scratchpad for code development with examples of function use cases.
'''

if __name__ == '__main__':
    ###################################################
    ### Generating a single transient with 2 pulses ###
    ###################################################
    if False:
        # Uses the data provided by Ken to get a pulse shape
        file_name = '../../data/pulse_spice.csv'
        pulse_mean = parse_pulse(file_name, scale=1)

        # 
        gen_pulses_spec = dict(t_diff = 10e-9,
                            fraction = 0.5,
                            pulse1 = pulse_mean,
                            pulse2 = pulse_mean,
                            threshold = 0,
                            t_start = 0,
                            sigma_noise = 0)

        transient_result = gen_pulses(**gen_pulses_spec)
        plt.plot(transient_result.keys(), transient_result.values())