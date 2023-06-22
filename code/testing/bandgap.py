import serial, time, minimalmodbus
import temp_chamber

import numpy as np
import matplotlib.pyplot as plt

def get_data(uC_port, temp_port="", chamber_port="", uC_precision=16, 
    vfsr=3.3, iterations=100, delay=1, channel=0):
    '''
    Inputs:
        uC_port: String. Microcontroller COM port.
        temp_port: String. TMP102 uC COM port. Empty string if not used.
        chamber_port: String. Temperature chamber COM port. Empty string if not 
            used.
        uC_precision: Integer. Number of bits for the microcontroller's analog read output.
        vfsr: Float. Full scale range voltage of the uC ADC used to 
            measure the bandgap voltage.
        iterations: Integer. Number of measurements to take. Note that
            the temperature will be sweeping over this time.
        delay: Float. Number of seconds to pause between readings.
        channel: 0 or 1. Which channel on the board to read from.
    Returns:
        uC_vec: List of floats. Internal temperature readings (C) from
            the microcontroller. Contains "iterations" elements.
        temp_vec: List of floats. Temperature readings (C) from the 
            ground truth TMP102 temperature sensor. Contains "iterations"
            elements if used, 0 otherwise.
        chamber_vec: List of floats. Temperature readings (C) from 
            the temperature chamber. Contains "iterations" elements if used,
            0 otherwise.
        vbg_vec: List of floats. Bandgap voltages (in V). Contains
            "iterations" elements.
    Notes:
        Return values are index-matched where applicable.
    '''
    use_TMP102 = (temp_port != "")
    use_chamber = (chamber_port != "")

    # assert use_TMP102 or use_chamber, "Must use either TMP102 or chamber"

    uC_vec = []
    temp_vec = []
    chamber_vec = []
    vbg_vec = []

    # Open serial connections
    uC_ser = serial.Serial(port=uC_port,
                        baudrate=19200,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS,
                        timeout=1)
    if use_chamber:
        chamber_ser = minimalmodbus.Instrument(chamber_port, 1)
        chamber_ser.serial.baudrate = 9600

    if use_TMP102:
        temp_ser = serial.Serial(port=temp_port,
                            baudrate=19200,
                            parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE,
                            bytesize=serial.EIGHTBITS,
                            timeout=1)


    # Sanity checking print statements
    disp_lst = ['uC Internal']
    if use_TMP102:
        disp_lst.append('TMP102')
    if use_chamber:
        disp_lst.append('Chamber')
    disp_lst.append('VBG')
    print('/'.join(disp_lst))

    # Take 'iterations' number of readings
    for i in range(iterations):
        # Trigger uC bandgap voltage reading
        uC_ser.write(b'scratch\n') # filler
        uC_ser.readline()
        cmd = f'bandgaptest{channel}\n'
        uC_ser.write(cmd.encode())

        # Trigger TMP102 temp reading if necessary
        if use_TMP102:
            temp_ser.write(b'temp\n')
            # print(temp_ser.readline())

        # Read internal temp from uC
        uC_val = 0 # float(uC_ser.readline())
        uC_vec.append(uC_val)

        # Read bandgap voltage from uC
        vbg_val = uC_ser.readline()
        vbg_val = int(vbg_val)/(2**uC_precision) * vfsr
        vbg_vec.append(vbg_val)

        # Read data from ground truth source(s)
        if use_TMP102:
            temp_val = temp_ser.readline()
            temp_vec.append(temp_val)
        
        if use_chamber:
            chamber_val = temp_chamber.read_temp(chamber_ser)
            chamber_vec.append(chamber_val)

        # Printing relevant values with each reading for sanity check
        disp_lst = [str(uC_val)]
        if use_TMP102:
            disp_lst.append(str(temp_val))
        if use_chamber:
            disp_lst.append(str(chamber_val))
        disp_lst.append(str(vbg_val))
        print('/'.join(disp_lst))

        # Pause between readings
        time.sleep(delay)

    uC_ser.close()
    
    if use_TMP102:
        temp_ser.close()
    
    if use_chamber:
        chamber_ser.serial.close()

    return uC_vec, temp_vec, chamber_vec, vbg_vec