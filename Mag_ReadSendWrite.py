#!/usr/bin/env python
# coding: utf-8

# In[1]:


import serial
import numpy as np
from ParseSerial import ReadSentence_Mag
import requests
import time
import sys
import h5py
import os


# In[2]:


#Starting with Influx 2.0, authorization tokens are necessary to access databases.
#The token can be accessed under the "Data" tab in the Influx UI.

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
measurement_name = 'mag_data'


# In[3]:


# connect to magnetometer
port ='/dev/ttyUSB6' 
baudrate=9600
mag = serial.Serial(port=port, baudrate=baudrate)


# In[4]:


header_mag = "0d"
splitline_mag = [4,8,12]
sentence_length_mag = 14


# In[6]:


#Number of data samples in each save file. Divide by 100 for seconds. (Magnetometer currently set to 20hz)
N = 585 * 60
dataCount = 0


# In[7]:


#Creating HDF5 datasets... maybe convert to for loop
timestr = time.strftime("%Y%m%d-%H%M%S")
directory = time.strftime("Mag-%Y-%m-%d")
os.mkdir("/home/user/tim-daq/data/"+directory)
magfile = h5py.File("/home/user/tim-daq/data/"+directory+"/Mag-"+timestr+".hdf5", "w", libver = 'latest')
x_dset = magfile.create_dataset("x", (N,), dtype='float', chunks = True, maxshape = (None,))
y_dset = magfile.create_dataset("y", (N,), dtype='float', chunks = True, maxshape = (None,))
z_dset = magfile.create_dataset("z", (N,), dtype='float', chunks = True, maxshape = (None,))
time_dset = magfile.create_dataset("time", (N,), dtype='int64', chunks = True, maxshape = (None,))
#filesnames_dset = magfile.create_dataset("filenames",(2,),dtype='', chunks= True, maxshape = (None,))


magfile.swmr_mode = True


# In[ ]:


while True:

    x_buff, y_buff, z_buff = ReadSentence_Mag(mag, header_mag, splitline_mag, sentence_length_mag) 
    #print(x_buff)
    current_point_time = int(round(time.time() * 1000000000))
    directory = time.strftime("Mag-%Y-%m-%d")
    current_line = '{measurement},location={location} mag_x={x},mag_y={y},mag_z={z} {timestamp}'.format(measurement=measurement_name,location=location_tag, x=x_buff,y=y_buff,z=z_buff, timestamp=current_point_time)       
    #print(current_line)
    r = requests.post(QUERY_URI, data=current_line, headers=headers)
    #print(r.status_code)
    
    if dataCount >= N:
        magfile.close()
        current_timestr = time.strftime("%Y%m%d-%H%M%S")
        magfile = h5py.File("/home/user/tim-daq/data/"+directory+"/Mag-"+current_timestr+".hdf5", "w", libver = 'latest')
        x_dset = magfile.create_dataset("x", (N,), dtype='float', chunks = True, maxshape = (None,))
        y_dset = magfile.create_dataset("y", (N,), dtype='float', chunks = True, maxshape = (None,))
        z_dset = magfile.create_dataset("z", (N,), dtype='float', chunks = True, maxshape = (None,))
        time_dset = magfile.create_dataset("time", (N,), dtype='int64', chunks = True, maxshape = (None,))
        magfile.swmr_mode = True
        dataCount = 0
   
    else:
       
        x_dset[dataCount] = x_buff
        y_dset[dataCount] = y_buff
        z_dset[dataCount] = z_buff
        time_dset[dataCount] = current_point_time
        
        x_dset.flush()
        y_dset.flush()
        z_dset.flush()
        time_dset.flush()
        dataCount += 1


# In[ ]:





# In[ ]:




