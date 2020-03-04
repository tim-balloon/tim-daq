"""
GOAL:
Write data from neat_speed_test.ino to InfluxDB, for plotting with Grafana.

Created Feb 2, 2020
Updated March 4, 2020

"""

import serial
import time
from influxdb import InfluxDBClient

client = InfluxDBClient('localhost', 8086, 'root', 'root', 'test')
ser = serial.Serial('/dev/cu.usbmodem14101')

while True:
    arduinoData = ser.readline().decode().strip() # reads data from serial port
    timestamp = str(int(round(time.time() * 1000000000))) # gives Unix nanosecond timestamp
    arduinoData_with_timestamp = arduinoData + " " + timestamp # appends timestamp to end of data string
    # print(arduinoData_with_timestamp) #can comment this out if you don't want all the strings printing in your terminal, since you can view the data through Grafana in real-time
    client.write_points([arduinoData_with_timestamp], protocol='line') # writes strings to InfluxDB database 'arduino'
