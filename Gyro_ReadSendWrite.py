"""
Reads data from DSP-1760 Gyroscope, sends into InfluxDB/Grafana for live plotting, and writes to HDF5.

Summer 2021
Tested On:
Starfire (ubuntu 18.04)
Influx 2.0.4
Grafana 7.4.2
"""


import serial
import numpy as np

#ParseSerial and cython_read can be used interchangeably for parsing. cython_read was written for speed improvements, but runs similarly. If using cython, use array splitline_gyro = [0, 8, 16, 24, 32, 40, 48, 50, 52, 56]. Otherwise splitline_gyro = [8, 16, 24, 32, 40, 48, 50, 52, 56]

#from ParseSerial import ReadSentence_Gyro 
from cython_read import ReadSentence_Gyro

import requests #For posting to influx
import time 
import sys
import h5py 
import os
import glob


"""---Authorization/QUERY initialization---"""
#Starting with Influx 2.0, authorization tokens are necessary to access databases
#The token can be accessed under the "Data" tab in the Influx UI.

#Stringing together query access
INFLUX_TOKEN='AjsrNgY_k97FMvgfCsgc2tPTx-lOVM-aYaCMjymNVIWpoSCkYh7H4AqIV9pLQHHk07zJa5pxTn4lo-3Ashwu5Q=='
ORG="tim@upenn"
INFLUX_CLOUD_URL='localhost'
BUCKET_NAME='sensors'

#Can change precision if needed. Currently set to nanoseconds (ns).
QUERY_URI='http://{}:8086/api/v2/write?org={}&bucket={}&precision=ns'.format(INFLUX_CLOUD_URL,ORG,BUCKET_NAME)

headers = {}
headers['Authorization'] = 'Token {}'.format(INFLUX_TOKEN)

#Parameters for line protocol that will be sent to Influx
location_tag = 'lab' 
measurement_name = 'gyro_data'


"""---Serial port initialization---"""
#Connecting to serial port. 
port = '/dev/ttyUSB1'
baudrate = 115200
gyro = serial.Serial(port=port, baudrate=baudrate)


"""---Parsing initilization---"""
#Parsing parameters used in ReadSentence_Gyro parse function
header_gyro = "fe81ff55"
splitline_gyro = [0,8, 16, 24, 32, 40, 48, 50, 52, 56]
sentence_length_gyro = 72


"""---HDF5 logging initilization---"""
#Number of data samples in each save file. Gyroscope currently set to 50hz.
N = 60000 
dataCount = 0 #Index counter

#Timestamps used for filenames.
timestr = time.strftime("%Y%m%d-%H%M%S")
datestamp = time.strftime("%Y-%m-%d-Gyro")

#First check if there is a folder with current date. If there isn't, create one.
if os.path.isdir("/home/user/tim-daq/data/"+datestamp) == 0:
    os.mkdir("/home/user/tim-daq/data/"+datestamp)

#Then check if the folder is empty. If it's empty, the first file number will start at 1.
#If the folder is not empty, check the file number of the last edited file, and add 1 to it for the new file. 
if len(os.listdir("/home/user/tim-daq/data/"+datestamp)) == 0:
    file_number = 1
    file_number_string =  str(1)
    
else:
    file_list = glob.glob("/home/user/tim-daq/data/"+datestamp+"/*.hdf5")
    latest_file = max(file_list, key=os.path.getctime)
    file_number = int(latest_file[-10:-5]) + 1
    file_number_string =  str(file_number)


#Create the HDF5 file and datasets
gyrofile = h5py.File("/home/user/tim-daq/data/"+datestamp+"/Gyro_"+timestr+"_"+file_number_string.zfill(5)+".hdf5", "w", libver = 'latest')

sn_dset = gyrofile.create_dataset("seq_num", (N,), dtype='i', chunks = True, maxshape = (None,))
x_dset = gyrofile.create_dataset("x", (N,), dtype='float32', chunks = True, maxshape = (None,))
y_dset = gyrofile.create_dataset("y", (N,), dtype='float32', chunks = True, maxshape = (None,))
z_dset = gyrofile.create_dataset("z", (N,), dtype='float32', chunks = True, maxshape = (None,))
st_dset = gyrofile.create_dataset("status", (N,), dtype='i', chunks = True, maxshape = (None,))
temp_dset = gyrofile.create_dataset("temp", (N,), dtype='float', chunks = True, maxshape = (None,))
time_dset = gyrofile.create_dataset("time", (N,), dtype='int64', chunks = True, maxshape = (None,))

#The index dataset keeps track of the index value of the latest data point recorded.
#This is helpful when we access the HDF5 file from another read program. The read program will know exactly which index to start reading from. 
#We can't use a "last_value()" function because the datasets are created with N empty spaces. 
index_dset = gyrofile.create_dataset("index", (1,), dtype='int64', chunks = True, maxshape = (None,)) 

#The filenames dataset stores the file name of the current and next file.
filenames_dset = gyrofile.create_dataset("filenames", (2,), dtype='int64', chunks = True, maxshape = (None,))

filenames_dset[0] = file_number
filenames_dset[1] = file_number + 1

#Must set swmr (single writer multiple reader) to true in order to read and write concurrently.
gyrofile.swmr_mode = True


"""---Main Loop---"""
while True:
    #Extracts data from parsing function
    sn_buff, x_buff, y_buff,z_buff, st_buff, temp_buff = ReadSentence_Gyro(gyro, header_gyro, splitline_gyro, sentence_length_gyro) 
    
    #Generates timestamp for Influx protocol
    current_point_time = int(round(time.time() * 1000000000))
    
    #Line protocol setup
    current_line = '{measurement},location={location} gyro_x={x},gyro_y={y},gyro_z={z},gyro_temp={temp} {timestamp}'.format(measurement=measurement_name,location=location_tag, x=x_buff,y=y_buff, z=z_buff,temp=temp_buff,timestamp=current_point_time)       
    #print(current_line)

    #Sends data into Influx
    r = requests.post(QUERY_URI, data=current_line, headers=headers) 
    #print(r.status_code) 
    

    #Generates new HDF5 file once datacount is reached. Identical file checking and creation to program startup. 
    if dataCount >= N:
        gyrofile.close() #Important to close current file!
        current_timestr = time.strftime("%Y%m%d-%H%M%S")
        datestamp = time.strftime("%Y-%m-%d-Gyro")
        
        
        if os.path.isdir("/home/user/tim-daq/data/"+datestamp) == 0:
            os.mkdir("/home/user/tim-daq/data/"+datestamp)  
        if len(os.listdir("/home/user/tim-daq/data/"+datestamp)) == 0:
            file_number_string =  str(1)
        else:
            file_list = glob.glob("/home/user/tim-daq/data/"+datestamp+"/*.hdf5")
            latest_file = max(file_list, key=os.path.getctime)
            file_number = int(latest_file[-10:-5]) + 1
            file_number_string =  str(file_number)
      
       
        gyrofile = h5py.File("/home/user/tim-daq/data/"+datestamp+"/Gyro_"+current_timestr+'_'+file_number_string.zfill(5)+".hdf5", "w", libver = 'latest')
        sn_dset = gyrofile.create_dataset("seq_num", (N,), dtype='i', chunks = True, maxshape = (None,))
        x_dset = gyrofile.create_dataset("x", (N,), dtype='float32', chunks = True, maxshape = (None,))
        y_dset = gyrofile.create_dataset("y", (N,), dtype='float32', chunks = True, maxshape = (None,))
        z_dset = gyrofile.create_dataset("z", (N,), dtype='float32', chunks = True, maxshape = (None,))
        st_dset = gyrofile.create_dataset("status", (N,), dtype='i', chunks = True, maxshape = (None,))
        temp_dset = gyrofile.create_dataset("temp", (N,), dtype='float', chunks = True, maxshape = (None,))
        time_dset = gyrofile.create_dataset("time", (N,), dtype='int64', chunks = True, maxshape = (None,))
        index_dset = gyrofile.create_dataset("index", (1,), dtype='int64', chunks = True, maxshape = (None,))
        filenames_dset = gyrofile.create_dataset("filenames", (2,), dtype='int64', chunks = True, maxshape = (None,))

        filenames_dset[0] = file_number
        filenames_dset[1] = file_number + 1
        gyrofile.swmr_mode = True
        dataCount = 0

    else:
        #If datacount isn't reached, continue adding latest data into the HDF5 datasets
        sn_dset[dataCount] = sn_buff
        x_dset[dataCount] = x_buff
        y_dset[dataCount] = y_buff
        z_dset[dataCount] = z_buff
        st_dset[dataCount] = st_buff
        temp_dset[dataCount] = temp_buff
        time_dset[dataCount] = current_point_time
        index_dset[0] = dataCount
        
        #Flushing is required to update datasets for reader programs
        sn_dset.flush()
        x_dset.flush()
        y_dset.flush()
        z_dset.flush()
        st_dset.flush()
        temp_dset.flush()
        index_dset.flush()
        
        dataCount += 1
    
    





