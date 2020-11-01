import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
from scipy import interpolate
import random
import pandas as pd
import warnings

def parse_tof_histogram(input_file, x_name='', y_names=[]):
    '''
    Inputs:
        input_file: String. CSV file where each column corresponds to a separate
                    histogram given the x-column. e.g.
                    TOF[ns] , MQ1   , MQ2   , ...
                    0.000   , 0     , 0     , ...
                    ...
                    1.000   , 10    , 12    , ...
        x_name:     String. Name of the column header for the x-axis of the histogram.
        y_names:    Collection of Strings. Names of the column headers for each 
                    separate histogram.
    Outputs:
        data_dict:  A dictionary of collections where the keys are the particle types
                    (column headers) and values are ToFs in seconds, e.g.
                    [1e-9, 1e-9, 1e-9, 2e-9, 2e-9, 2e-9]
    '''
    data = pd.read_csv(input_file)
    times = list(data[x_name])
    data_dict = {y:[] for y in y_names}

    for y in y_names:
        for i in range(len(times)):
            data_dict[y] = data_dict[y] + [times[i]*1e-9]*int(data[y][i]*1000)

    return data_dict

def parse_pulse(input_file, time_name='time', signal_name='signal'):
    '''
    Inputs:
        input_file:     String. CSV file with times and signal values in the columns
                        time,signal
                        t_0, s_0,
                        t_1, s_1,
                        ...
        time_name:      String. Name of the column header for time values.
        signal_name:    String. Name of the column header for signal values.
    Outputs:
        pulse_dict: Dictionary of float:float where the key:values are time:signal.
    '''
    data = pd.read_csv(input_file)
    times = list(data[time_name])
    values = list(data[signal_name])
    pulse_dict = dict()
    for i in range(len(times)):
        pulse_dict[times[i]] = values[i]

    return pulse_dict

def get_t_trigger(pulse, fraction, scale=1):
    '''
    Inputs:
        pulse:      Dictionary of float:float where the key:values are time:signal. 
        fraction:   Float (0,1] corresponding to where an ideal CFD would
                    indicate a rising edge.
        scale:      Multiplies every value in the pulse by a scale factor.
    Outputs:
        t_trigger:  Float. Time (using linear interpolation) corresponding to 
                    when an ideal constant fraction discriminator would spit out
                    a rising edge.
    Notes:
        Assumes no more than 1 crossing of the fractional value before the peak value.
    '''
    # Splitting times and values because I use indices later
    times = list(pulse.keys())
    times.sort()
    values = [pulse[t]*scale_factor for t in times]

    # Peak value and its index
    peak_value = max(values)
    peak_index = np.argmax(values)

    # CFD trigger value
    v_trigger = peak_value * fraction

    # Looking only at the pre-peak indices for the rise time trigger
    times_rising = times[0:peak_index]
    values_rising = values[0:peak_index]

    # Finding the nearest point 
    nearest_discretized_index = (np.abs(np.array(values_rising)-v_trigger)).argmin()

    # Linear interpolation between data points
    t_low = 0
    t_high = np.inf

    if values_rising[nearest_discretized_index] >= v_trigger:
        t_high = times_rising[nearest_discretized_index]
        t_low = times_rising[nearest_discretized_index-1]
        v_high = values_rising[nearest_discretized_index]
        v_low = values_rising[nearest_discretized_index-1]
    else:
        t_low = times_rising[nearest_discretized_index]
        t_high = times_rising[nearest_discretized_index+1]
        v_low = values_rising[nearest_discretized_index]
        v_high = values_rising[nearest_discretized_index+1]

    t_trigger = np.interp(v_trigger, [v_low, v_high], [t_low, t_high])
    return t_trigger

def gen_pulses(t_diff, fraction, pulse1, pulse2, threshold=0, t_start=0, 
        sigma_noise=0):
    '''
    Inputs:
        t_diff:         Float. Time difference between pulse rising edges in seconds.
        fraction:       Float in (0,1] corresponding to where an ideal CFD 
                        would indicate a rising edge.
        pulse1:         Dictionary of float:float where the keys are a given time 
                        and the values are the signal values. First pulse shape.
                        Time MUST start at 0.
        pulse2:         Dictionary of float:float where the keys are a given time
                        and the values are the signal values. Second pulse shape.
                        Time MUST start at 0.
        threshold:      Float. Minimum threshold (for calculating noise tolerance
                        later) for the thing to even consider returning a rising edge.
        t_start:        Float. Time for the first pulse to begin.
        sigma_noise:    Float. Standard deviation of Gaussian white noise.
    Outputs:
        transient_result:   Dictionary of float:float where the keys are time
                            and the values are the signal value. 
    Raises:
        AssertionError: If the pulse timing doesn't start at time 0.
        AssertionError: If the start time for the first pulse is < 0.
    Notes:
        Currently threshold and sigma_noise are unused.
    '''
    assert (min(pulse1.keys())==0 and min(pulse2.keys())==0), \
        'Pulse timing must start at 0.'

    assert t_start >= 0, 'Start time for the pulse must be no less than 0'

    # When the CFD is supposed to pulse
    t_trigger1 = get_t_trigger(pulse1, fraction)
    t_trigger2 = t_trigger1 + t_diff

    # When to start pulse1 and pulse2
    t_start1 = t_start
    t_start2 = t_trigger2 - get_t_trigger(pulse2, fraction)

    # Separating pulse times and values for convenience
    times_pulse1 = list(pulse1.keys())
    times_pulse1.sort()
    values_pulse1 = [pulse1[t] for t in times_pulse1]

    times_pulse2 = list(pulse2.keys())
    times_pulse2.sort()
    values_pulse2 = [pulse2[t] for t in times_pulse2]

    # Create one timing setup with only the first pulse and one with only the second
    # This is in case of overlap; we'll interpolate and choose the max between the two
    if t_start == 0:
        times_only1 = times_pulse1
        values_only1 = values_pulse1
    else:
        times_only1 = [0] + list(times_pulse1)
        values_only1 = [0] + list(values_pulse1)

    times_only1 = times_only1 + [max(times_only1)+min(times_only1[1:]), t_start2 + max(times_pulse2)]
    values_only1 = values_only1 + [0,0]

    times_only2 = [0, t_start2-min(times_pulse2[1:])] + [t_start2+t for t in times_pulse2]
    values_only2 = [0, 0] + values_pulse2   

    if t_start2 <= t_start + max(times_pulse1):
        warnings.warn('Provided second pulse shape overlaps with first pulse. Results may be nonsensical')
    
    interp_only1 = interpolate.interp1d(times_only1, values_only1)
    interp_only2 = interpolate.interp1d(times_only2, values_only2)

    times = list(set(times_only1 + times_only2))
    times.sort() # Not sorting gives you horrible, horrible-looking outputs
    values = [max(interp_only1(t), interp_only2(t)) for t in times]

    # Translating into a final transient result to feed into Cadence
    transient_result = dict()

    for i in range(len(times)):
        transient_result[times[i]] = values[i]

    return transient_result


def write_transient_file(data, output_file):
    '''
    Inputs:
        data:           Dictionary where each key:value pair has the key as
                        the time, and the value is the output value (voltage, 
                        current, whatever).
        output_file:    String. Path to the desired output file.
    Outputs:
        No returned values. Writes the relevant information to
        'output_file'.
    Notes:
        Untested.
    '''
    times = list(data.keys())
    times.sort()
    values = [data[t] for t in times]

    with open(output_file, 'w') as f:
        for t in times:
            f.write('{:.20g} {:.20g}\n'.format(t, data[t]))

if __name__ == "__main__":
    print("Hello, world!")
