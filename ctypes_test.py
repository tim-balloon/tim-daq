"""

Using ctypes to wrap C parsing function and run in python. 
Function can be found in CSerialParser.c


"""

import ctypes
import time
import os



my_lib = ctypes.CDLL("/home/user/tim-daq/CSerialLibrary.so") #Loading shared library.
#Shared libraries can be compiled with

# cc -fPIC -shared -o libsum.so PROGRAM_NAME.c

#Creating a class to match C program's return values. 
class TUPLE(ctypes.Structure):
    _fields_ = [("x",ctypes.c_float),("y",ctypes.c_float),("z",ctypes.c_float),("seq_num",ctypes.c_int),("temp",ctypes.c_int)]

#Setting return type attribrute of c function
my_lib.read_gyro.restype = ctypes.c_void_p
my_lib.init_gyro_port.restype = ctypes.c_int

count = 0

ser_port = my_lib.init_gyro_port()

while True:
    time.sleep(.02)
    
    read_tuple = TUPLE.from_address(my_lib.read_gyro(ser_port))

    #print("X:",round(read_tuple.x,8),"Y:",round(read_tuple.y,8),"Z: ",round(read_tuple.z,8), "Temp:",read_tuple.temp, "Seq:",read_tuple.seq_num)
    count += 1
    print(count)
    #my_lib.free_tuple(ctypes.byref(read_tuple))
    del read_tuple
