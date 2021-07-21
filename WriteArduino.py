import serial
import numpy as np


port='/dev/ttyACM0'
baudrate=115200

ser = serial.Serial(port=port, baudrate=baudrate)

operate=True
while(operate):
    var = input("Enter command to transmit, H for help, Q to quit: ")
    if not var == 'Q':
        ser.write(bytearray((var+'\n').encode()))
        #for i in np.arange(10):
        #    print(ser.readline())
    else:
        operate=False
