import serial, time, temp_chamber
import numpy as np
import matplotlib.pyplot as plt

def get_data(teensy_port, temp_port, teensy_precision=16, vfsr=3.3, iterations=100,
        delay=1):
    '''
    Inputs:
        teensy_port: String. Teensy COM port.
        temp_port: String. Temperature sensor COM port.
        teensy_precision: Integer. Number of bits for the Teensy's output.
        vfsr: Float. Full scale range voltage of the Teensy ADC used to 
            measure the bandgap voltage.
        iterations: Integer. Number of measurements to take. Note that
            the temperature will be sweeping over this time.
        delay: Float. Number of seconds to pause between readings.
    Returns:
        teensy_vec: List of floats. Internal temperature readings from
            the Teensy. Contains "iterations" elements.
        temp_vec: List of floats. Temperature readings from the 
            ground truth temperature sensor. Contains "iterations"
            elements.
        vbg_vec: List of floats. Bandgap voltages (in V). Contains
            "iterations" elements.
    Notes:
        Return values are index-matched.
    '''
    # Open serial connections
    teensy_ser = serial.Serial(port=teensy_port,
                        baudrate=19200,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS,
                        timeout=1)
    temp_ser = minimalmodbus.Instrument(temp_port, 1)
    temp_ser.serial.baudrate = 9600
    # temp_ser = serial.Serial(port=temp_port,
    #                     baudrate=19200,
    #                     parity=serial.PARITY_NONE,
    #                     stopbits=serial.STOPBITS_ONE,
    #                     bytesize=serial.EIGHTBITS,
    #                     timeout=1)

    teensy_vec = []
    temp_vec = []
    vbg_vec = []

    for i in range(iterations):
        # Trigger Teensy and gnd truth reading
        teensy_ser.write(b'bandgaptest\n')
        # temp_ser.write(b'temp\n')

        # Read data from Teensy
        teensy_vec.append(teensy_ser.readline())

        vbg = float(teensy_ser.readline())/(2**teensy_precision) * vfsr
        vbg_vec.append(vbg)

        # Read data from gnd truth
        # temp_vec.append(temp_ser.readline())
        temp_vec.append(temp_chamber.read_temp(temp_ser, 1))

        time.sleep()

    teensy_ser.close()
    # temp_ser.close()
    temp_ser.serial.close()

    return teensy_vec, temp_vec, vbg_vec