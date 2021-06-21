#!/usr/bin/env python
# coding: utf-8

# In[1]:


import serial
import numpy as np
import h5py
import time
import math
import requests
import sys
import os
import glob


# In[2]:


#Starting with Influx 2.0, authorization tokens are necessary to access databases

#Stringing together query access
INFLUX_TOKEN='AjsrNgY_k97FMvgfCsgc2tPTx-lOVM-aYaCMjymNVIWpoSCkYh7H4AqIV9pLQHHk07zJa5pxTn4lo-3Ashwu5Q=='
ORG="tim@upenn"
INFLUX_CLOUD_URL='localhost'
BUCKET_NAME='sensors'

QUERY_URI='http://{}:8086/api/v2/write?org={}&bucket={}&precision=ns'.format(INFLUX_CLOUD_URL,ORG,BUCKET_NAME)

headers = {}
headers['Authorization'] = 'Token {}'.format(INFLUX_TOKEN)

#Line protocol
location_tag = 'lab'
measurement_name = 'heading'


# In[3]:

start_time = time.perf_counter()
datestamp = time.strftime("%Y-%m-%d")
declination = 11

#A series of directory checks. Will exit from program if no folder/files are detected.
if os.path.isdir("/home/user/tim-daq/data/"+datestamp+"-Mag") == 0:
    print("No Directory Detected")
    sys.exit()
    
if os.path.isdir("/home/user/tim-daq/data/"+datestamp+"-Inclin") == 0:
    print("No Directory Detected")
    sys.exit()
if os.path.isdir("/home/user/tim-daq/data/"+datestamp+"-Stepper") == 0:
    print("No Directory Detected")
    sys.exit()


if len(os.listdir("/home/user/tim-daq/data/"+datestamp+"-Mag")) == 0:
    print("No Files Detected")
    sys.exit()
else:
    file_list = glob.glob("/home/user/tim-daq/data/"+datestamp+"-Mag/*.hdf5")
    mag_file_name = max(file_list, key=os.path.getctime)
    #print(mag_file_name)
    
if len(os.listdir("/home/user/tim-daq/data/"+datestamp+"-Inclin")) == 0:
    print("No Files Detected")
    sys.exit()
else:
    file_list = glob.glob("/home/user/tim-daq/data/"+datestamp+"-Inclin/*.hdf5")
    inclin_file_name = max(file_list, key=os.path.getctime)
    #print(inclin_file_name)
if len(os.listdir("/home/user/tim-daq/data/"+datestamp+"-Stepper")) == 0:
    print("No Files Detected")
    sys.exit()
else:
    file_list = glob.glob("/home/user/tim-daq/data/"+datestamp+"-Stepper/*.hdf5")
    stepper_file_name = max(file_list, key=os.path.getctime)
    #print(inclin_file_name)
      
        
mag_file = h5py.File(mag_file_name, 'r', libver = 'latest', swmr = True)
inclin_file = h5py.File(inclin_file_name, 'r', libver = 'latest', swmr = True)
stepper_file = h5py.File(stepper_file_name, 'r', libver = 'latest', swmr = True)


mag_x = mag_file['x']
mag_len = mag_x.shape[0]
mag_y = mag_file['y']
mag_z = mag_file['z']
mag_timestamp = mag_file['time']

inclin_x = inclin_file['x']
inclin_y = inclin_file['y']
inclin_len = inclin_x.shape[0]

stepper_az = stepper_file['az']
stepper_el = stepper_file['el']
stepper_len = stepper_az.shape[0]

mag_heading_list = []
true_heading_list = []
el_list = []
zero_mag_deg = 0
zero_true_deg = 0
zero_el = 0
# In[4]:


while True:
    
	
    #Grabs the latest data point index (from file dataset)
    mag_index_num = mag_file['index'][0] 
    inclin_index_num = inclin_file['index'][0]
    stepper_index_num = stepper_file['index'][0]
    
    #Must refresh constantly..
    mag_x.id.refresh()
    mag_y.id.refresh()
    mag_z.id.refresh()
    mag_timestamp.refresh()
    
    inclin_x.id.refresh()
    inclin_y.id.refresh()

    stepper_az.id.refresh()
    stepper_el.id.refresh()
    
    #Creates list copies (much faster than list()..?)
    mag_x_list = mag_x[:]
    mag_y_list = mag_y[:]
    mag_z_list = mag_z[:]
    mag_timestamp_list = mag_timestamp[:]
    inclin_x_list = inclin_x[:]
    inclin_y_list = inclin_y[:]
    stepper_az_list = stepper_az[:]
    stepper_el_list = stepper_el[:]
    
    #Grabs latest data values
    mag_x_dat = mag_x_list[mag_index_num]
    mag_y_dat = mag_y_list[mag_index_num]
    mag_z_dat = mag_z_list[mag_index_num]
    mag_timestamp_dat = mag_timestamp_list[mag_index_num]
    
    inclin_x_dat = inclin_x_list[inclin_index_num]
    inclin_y_dat = inclin_y_list[inclin_index_num]

    stepper_az_dat = stepper_az_list[stepper_index_num]
    stepper_el_dat = stepper_el_list[stepper_index_num]
    
    
	
    #Heading calculations
    
    pitch = np.deg2rad(inclin_y_dat)
    
    roll = -np.deg2rad(inclin_x_dat)
        
    Xh = mag_x_dat * np.cos(pitch) + mag_y_dat * np.sin(roll) * np.sin(pitch) - mag_z_dat * np.cos(roll) * np.sin(pitch)
    
    Yh = mag_y_dat * np.cos(roll) + mag_z_dat * np.sin(roll)
    
    #print(np.rad2deg(pitch), np.rad2deg(roll))
    #heading = np.rad2deg(math.atan2(mag_y_dat,mag_x_dat))
    magnetic_north = np.rad2deg(math.atan2(Yh,Xh))
    true_north = magnetic_north - declination
    if magnetic_north < 0:
        magnetic_north += 360
    if true_north < 0:
        true_north += 360
    while time.perf_counter() - start_time< .01:
        mag_heading_list.append(magnetic_north)
        true_heading_list.append(true_north)
        el_list.append(inclin_x_dat)
        zero_mag_deg = mag_heading_list[-1]
        zero_true_deg = true_heading_list[-1]
        zero_el = el_list[-1]
        
    print(stepper_az_dat)
    print(stepper_el_dat)
    stepper_heading_mag = zero_mag_deg - stepper_az_dat
    if stepper_heading_mag < 0:
        stepper_heading_north += 360
    stepper_elevation = zero_el - stepper_el_dat

    line = '{measurement},location={location} mag_heading={heading},true_heading={heading2},stepper_heading_mag={heading3},elevation={elevation} {timestamp}'.format(measurement=measurement_name,location=location_tag, heading=magnetic_north,heading2=true_north,heading3 = stepper_heading_mag,elevation = stepper_elevation, timestamp=mag_timestamp_dat)
    r = requests.post(QUERY_URI, data=line, headers=headers)
    #print(r.status_code)
    #print(line)
    
    
    #Once the end of the file has been reached, get ready to open the new one.
    if mag_index_num >= mag_len - 2:
        next_file_num = mag_file['filenames'][1] #Next file number taken from current open file
        next_file = str(next_file_num)
    
        mag_index_num = 0
        mag_file.close() #Close current file
        
        #Check if the next file (with correct number) exists
        file_path = "/home/user/tim-daq/data/"+datestamp+"-Mag/"+"*"+next_file.zfill(5)+"*"
        while glob.glob(file_path) == []: #If it doesn't exist, wait
            time.sleep(0.05)
        
        #Opens the next HDF5 file
        mag_file = h5py.File(glob.glob(file_path)[0], 'r', libver = 'latest', swmr = True)
        mag_x = mag_file['x']
        mag_len = mag_x.shape[0]
        mag_y = mag_file['y']
        mag_z = mag_file['z']
        mag_timestamp = mag_file['time']
    
    if inclin_index_num >= inclin_len - 2:
        next_file_num = inclin_file['filenames'][1]
        next_file = str(next_file_num)
        inclin_index_num = 0
        inclin_file.close()
        
        file_path = "/home/user/tim-daq/data/"+datestamp+"-Inclin/"+"*"+next_file.zfill(5)+"*"
        while glob.glob(file_path) == []:
            time.sleep(0.05)     
        
        inclin_file = h5py.File(glob.glob(file_path)[0], 'r', libver = 'latest', swmr = True)
        inclin_x = inclin_file['x']
        inclin_len = inclin_x.shape[0]
        inclin_y = inclin_file['y'] 
        inclin_timestamp = mag_file['time']
        

    
    
    
    
    #print(x_data[np.max(np.flatnonzero(x_data))])
    #print(mag_x_dat,mag_y_dat,mag_z_dat,"  ",inclin_x_dat,inclin_y_dat)

