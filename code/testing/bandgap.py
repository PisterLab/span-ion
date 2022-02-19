import serial
import numpy as np
import matplotlib.pyplot as plt

def get_data(com_port):
    '''
    Inputs: DOCUMENT THIS, DUDE
    '''
    ser = serial.Serial(port=com_port,
                        baudrate=9600,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS)

    ser.write(b'bandgaptest\n')
    num = 1
    list_volt = list([])
    list_temp =
    while num != 20:
        volt_line = ser.readline()
        temp_line = ser.readline()
        str_volt_line = volt_line.decode('utf-8')
        num_volt_line = int(str_volt_line)
        list_volt = list_volt + [num_volt_line]
        str_temp_line = temp_line.decode('utf-8')
        num_volt_line = int(str_temp_line)
        list_temp = list_temp + [num_volt_line]

    #plot
    plt.plot(list_temp, list_volt,label='bandgap vs temperature',color='red',linewidth=2)
    plt.xlabel('Temperature (Teensy)')
    plt.ylabel('Voltage (V)')
    plt.show()