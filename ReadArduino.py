"""
Reads from stepper motors connected to Arduino, sends into InfluxDB/Grafana for live plotting, and writes to HDF5.

Summer 2021
Tested On:
Starfire (ubuntu 18.04)
Influx 2.0.4
Grafana 7.4.2
"""

import serial
import numpy as np
import requests
import time
import h5py
import sys
import os
import glob

"""---Authorization/QUERY initialization---"""
#Starting with Influx 2.0, authorization tokens are necessary to access databases

#Stringing together query access
INFLUX_TOKEN='IHZnow202XDvTxMu_D5pzcUncDXtiDCD7B_sb-OOaf1garA4LUYkwJrVVes4r0jGLsUlkdq66hTgLEqwtQ9mQQ=='
ORG="tim@upenn"
INFLUX_CLOUD_URL='localhost'
BUCKET_NAME='sensors'

#Can change precision if needed. Currently set to nanoseconds (ns).
QUERY_URI='http://{}:8086/api/v2/write?org={}&bucket={}&precision=ns'.format(INFLUX_CLOUD_URL,ORG,BUCKET_NAME)

headers = {}
headers['Authorization'] = 'Token {}'.format(INFLUX_TOKEN)

#Parameters for line protocol that will be sent to Influx
location_tag = 'lab'
measurement_name = 'stepper_data'


"""---Serial port initialization---"""
#Connecting to serial port. 
port='/dev/ttyACM2'
baudrate=115200
ser = serial.Serial(port=port, baudrate=baudrate)

"""---HDF5 logging initilization---"""
#Number of data samples in each save file. Arduino readout currently set to 250hz.
N = 60000
dataCount = 0

current_line = [0,0,0,0]


#Timestamps used for filenames.
timestr = time.strftime("%Y%m%d-%H%M%S")
datestamp = time.strftime("%Y-%m-%d-Stepper")

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
stepperfile = h5py.File("/home/user/tim-daq/data/"+datestamp+"/Stepper_"+timestr+"_"+file_number_string.zfill(5)+".hdf5", "w", libver = 'latest')

az_dset = stepperfile.create_dataset("az", (N,), dtype='float32', chunks = True, maxshape = (None,))
el_dset = stepperfile.create_dataset("el", (N,), dtype='float32', chunks = True, maxshape = (None,))
time_dset = stepperfile.create_dataset("time", (N,), dtype='int64', chunks = True, maxshape = (None,))

#The index dataset keeps track of the index value of the latest data point recorded.
#This is helpful when we access the HDF5 file from another read program. The read program will know exactly which index to start reading from. 
#We can't use a "last_value()" function because the datasets are created with N empty spaces. 
index_dset = stepperfile.create_dataset("index", (1,), dtype='int64', chunks = True, maxshape = (None,))

#The filenames dataset stores the file name of the current and next file.
filenames_dset = stepperfile.create_dataset("filenames", (2,), dtype='int64', chunks = True, maxshape = (None,))

filenames_dset[0] = file_number
filenames_dset[1] = file_number + 1

#Must set swmr (single writer multiple reader) to true in order to read and write concurrently.
stepperfile.swmr_mode = True


"""---Main Loop---"""
while True:
    data = str(ser.readline()).replace("b'","").replace("\\r\\n'","") #Cleans up readouts from Arduino
    split_data = data.split(",") #Split serial data using comma delimiter
    az_conv = 0
    el_conv=0
    
    #Only accepts data if all values are reading correctly
    if len(split_data) == 4:
        try:
            az_raw=int(split_data[2])
            el_raw=int(split_data[3])
        except:
            pass
        az_conv =az_raw*360/(200*16*8) #Converting steps into degrees
        el_conv =el_raw*360/(200*16*20)
    
        time_stamp = int(round(time.time() * 1000000000)) #Generates timestamp for Influx protocol 

        #Line protocol setup
        current_line = '{measurement},location={location} az={az},el={el} {timestamp}'.format(measurement=measurement_name,location=location_tag,az=az_conv,el=el_conv, timestamp=time_stamp)     
        print(current_line + ' ' + split_data[1])
        
        #Sends data into Influx
        r = requests.post(QUERY_URI, data=current_line, headers=headers)
        #print(r.status_code)
    

    #Generates new HDF5 file once datacount is reached. Identical file checking and creation to program startup. 
    if dataCount >= N:
        stepperfile.close()  #Important to close current file!
        current_timestr = time.strftime("%Y%m%d-%H%M%S")
        datestamp = time.strftime("%Y-%m-%d-Stepper")
        
        if os.path.isdir("/home/user/tim-daq/data/"+datestamp) == 0:
            os.mkdir("/home/user/tim-daq/data/"+datestamp)  
        if len(os.listdir("/home/user/tim-daq/data/"+datestamp)) == 0:
            file_number = 1
            file_number_string =  str(1)
        else:
            file_list = glob.glob("/home/user/tim-daq/data/"+datestamp+"/*.hdf5")
            latest_file = max(file_list, key=os.path.getctime)
            file_number = int(latest_file[-10:-5]) + 1
            file_number_string =  str(file_number)
        
        
       
        stepperfile = h5py.File("/home/user/tim-daq/data/"+datestamp+"/Stepper_"+current_timestr+'_'+file_number_string.zfill(5)+".hdf5", "w", libver = 'latest')
        az_dset = stepperfile.create_dataset("az", (N,), dtype='float32', chunks = True, maxshape = (None,))
        el_dset = stepperfile.create_dataset("el", (N,), dtype='float32', chunks = True, maxshape = (None,))
        time_dset = stepperfile.create_dataset("time", (N,), dtype='int64', chunks = True, maxshape = (None,))
        index_dset = stepperfile.create_dataset("index", (1,), dtype='int64', chunks = True, maxshape = (None,))
        filenames_dset = stepperfile.create_dataset("filenames", (2,), dtype='int64', chunks = True, maxshape = (None,))

        filenames_dset[0] = file_number
        filenames_dset[1] = file_number + 1
        stepperfile.swmr_mode = True
        dataCount = 0
    else:
        #If datacount isn't reached, continue adding latest data into the HDF5 datasets
        az_dset[dataCount] = az_conv
        el_dset[dataCount] = el_conv
        
        time_dset[dataCount] = time_stamp
        index_dset[0] = dataCount
        
        #Flushing is required to update datasets for reader programs
        az_dset.flush()
        el_dset.flush()
        
        index_dset.flush()
        
        dataCount += 1
        

        
       

       
    
        
