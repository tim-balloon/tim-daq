# GOAL:
# Read temperature sensor data from Arduino serial port and forward to InfluxDB
# database 'arduino'. Note that temperature sensor data is formatted into
# strings that follow InfluxDB's line protocol in the Arduino sketch code, but
# DOES NOT INCLUDE TIMESTAMP on the Arduino side! Timestamp must be added here.

# InfluxDB line protocol syntax:
# <measurement>[,<tag_key>=<tag_value>[,<tag_key>=<tag_value>]] <field_key>=<field_value>[,<field_key>=<field_value>] [<timestamp>]
# E.g. Temp_Sensor,pin=A0 voltage=0.68,Celsius=17.87,Fahrenheit=64.17 1466625759000000000
# More info on the line protocol here:
# https://docs.influxdata.com/influxdb/v1.7/write_protocols/line_protocol_reference/

# Note: Need to install InfluxDB python library (along w/ Grafana and InfluxDB) - info at 
#       https://influxdb-python.readthedocs.io/en/latest/include-readme.html
#       This code was written for and used with MacOS, certain things may work
#       differently on other operating systems.

import argparse # needed to specify database in command line
import serial # needed to read from serial port
import time # needed for timestamps

from influxdb import InfluxDBClient

# argparser
parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument('-H', '--host', default='localhost:8086')
parser.add_argument('-D', '--database', required=True) # allows selection of database from the command line
args = parser.parse_args()

# Starts InfluxDB
client = InfluxDBClient('localhost', 8086, 'root', 'root', args.database) #potential improvement: configure this to allow for selection of custom port using args.host?
client.get_list_database() # same as 'SHOW DATABASES' command in InfluxDB
client.switch_database(args.database) # same as 'USE database' command in InfluxDB, i.e. selects database that data will be stored in
# client.create_database(args.database) <-- use this instead if database does not already exist

# Reads data from serial + writes to InfluxDB!
# Note that serial port will be different on other operating systems!
ser = serial.Serial('/dev/cu.usbmodem14101') # potential improvement: code to manually/automatically search for & select serial port?

while True:
    arduinoData = ser.readline().decode().strip() # reads data from serial port

    timestamp = str(int(round(time.time() * 1000000000))) # gives Unix nanosecond timestamp
    arduinoData_with_timestamp = arduinoData + " " + timestamp # appends timestamp to end of data string

    print(arduinoData_with_timestamp) #can comment this out if you don't want all the strings printing in your terminal, since you can view the data through Grafana in real-time
    client.write_points([arduinoData_with_timestamp], protocol='line') # writes strings to InfluxDB database 'arduino'

# Other things that can be done:
# 1) Write data strings to separate text file (not rlly necessary since you can
#    just view all the data in InfluxDB by commanding SELECT * FROM <measurement>
#    e.g. SELECT * from Temp_Sensor)
# 2) Threading
