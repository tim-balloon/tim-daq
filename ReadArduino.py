import serial
import numpy as np
import requests
import time
import h5py
import sys
import os
import glob

#Starting with Influx 2.0, authorization tokens are necessary to access databases

#Stringing together query access
INFLUX_TOKEN='IHZnow202XDvTxMu_D5pzcUncDXtiDCD7B_sb-OOaf1garA4LUYkwJrVVes4r0jGLsUlkdq66hTgLEqwtQ9mQQ=='
ORG="tim@upenn"
INFLUX_CLOUD_URL='localhost'
BUCKET_NAME='sensors'

QUERY_URI='http://{}:8086/api/v2/write?org={}&bucket={}&precision=ns'.format(INFLUX_CLOUD_URL,ORG,BUCKET_NAME)

headers = {}
headers['Authorization'] = 'Token {}'.format(INFLUX_TOKEN)

#Line protocol
location_tag = 'lab'
measurement_name = 'stepper_data'

port='/dev/ttyACM0'
baudrate=115200

ser = serial.Serial(port=port, baudrate=baudrate)

N = 600000 
dataCount = 0

current_line = [0,0,0,0]


#Creating HDF5 datasets... maybe convert to for loop
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

stepperfile = h5py.File("/home/user/tim-daq/data/"+datestamp+"/Stepper_"+timestr+"_"+file_number_string.zfill(5)+".hdf5", "w", libver = 'latest')
az_dset = stepperfile.create_dataset("az", (N,), dtype='float32', chunks = True, maxshape = (None,))
el_dset = stepperfile.create_dataset("el", (N,), dtype='float32', chunks = True, maxshape = (None,))
time_dset = stepperfile.create_dataset("time", (N,), dtype='int64', chunks = True, maxshape = (None,))
index_dset = stepperfile.create_dataset("index", (1,), dtype='int64', chunks = True, maxshape = (None,))
filenames_dset = stepperfile.create_dataset("filenames", (2,), dtype='int64', chunks = True, maxshape = (None,))

filenames_dset[0] = file_number
filenames_dset[1] = file_number + 1

stepperfile.swmr_mode = True



while True:
    data = str(ser.readline()).replace("b'","").replace("\\r\\n'","")
    split_data = data.split(",")
    az_conv = 0
    el_conv=0
    time_stamp = int(round(time.time() * 1000000000))
    if len(split_data) == 4:
        az_raw=int(split_data[2])
        el_raw=int(split_data[3])
        az_conv =az_raw*360/(200*16*8)
        el_conv =el_raw*360/(200*16*20)
    
        
        current_line = '{measurement},location={location} az={az},el={el} {timestamp}'.format(measurement=measurement_name,location=location_tag,az=az_conv,el=el_conv, timestamp=time_stamp)     
        print(current_line + ' ' + split_data[1])
        r = requests.post(QUERY_URI, data=current_line, headers=headers)
        #print(r.status_code)

    if dataCount >= N:
        stepperfile.close()
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
        
        az_dset[dataCount] = az_conv
        el_dset[dataCount] = el_conv
        
        time_dset[dataCount] = time_stamp
        index_dset[0] = dataCount
        
        az_dset.flush()
        el_dset.flush()
        
        index_dset.flush()
        
        dataCount += 1
        

        
       

       
    
        
