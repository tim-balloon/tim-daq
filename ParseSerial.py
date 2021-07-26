"""
Parsing functions for the gyroscope, inclinometer, and magnetometer. 
Converts serial transmission into readable values. 
"""

import numpy as np
import serial 
import struct
import time


def hexToFloat(value): 
    """Converts hexadecimal to floating point for gyro x,y,z readings  
    :param value: string (4 hexadecimal digits)
    """
    return struct.unpack('!f', bytes.fromhex(value))[0] 

def s16(value): 
    """Converts hex into signed decimal from 2's complement
    :param value: integer 
    """
    return -(value & 0x8000) | (value & 0x7fff) 

        
def ReadSentence_Gyro(ser, header, splitline, sentence_length):
    """Converts serial transmission from gyroscope into readable values. 
    :param ser: serial.serial() serial port indicator
    :param header: string of header characters
    :param splitline: array of integers that indicate different values based on character location
    :param sentence_length: integer 
    """

    buf = ''
    sentence = ''
    
    reading_sentence = False
    sentence_complete = False
    
    while not sentence_complete: 
        
        if len(sentence) == sentence_length - len(header): #Check if expected sentence length is reached (minus header length)         
            sentence_complete = True    
            #Splitting the readout "sentence" based on character position (splitline)    
            split_result = [sentence[i:j] for i, j in zip([0] + splitline, splitline + [None])]
        
        else:
            onebyte = ser.read().hex() #Reading bytes from serial port and adding to buffer          
            buf += onebyte 
            
            if reading_sentence: # if start bytes found on last pass...
                # start acculumlating the data 
                sentence += onebyte
                
            if header in buf: #Check if header has appeared. If so, begin generating a "sentence" of data                 
                reading_sentence = True
                
    return (int(split_result[7],16), #sequence number
            hexToFloat(split_result[0]), # x
            hexToFloat(split_result[1]), # y
            hexToFloat(split_result[2]), # z
            int(split_result[6],16), # status
            int(split_result[8],16)) # temperature

def ReadSentence_Inclin(ser, header, splitline, sentence_length):
    """Converts serial transmission from inclinometer into readable values. 
    :param ser: serial.serial() serial port indicator
    :param header: string of header characters
    :param splitline: array of integers that indicate different values based on character location
    :param sentence_length: integer 
    """

    buf = ''
    sentence = ''
    x = 0.0
    y = 0.0
    temp = 0.0
    reading_sentence = False
    sentence_complete = False
    
    while not sentence_complete:       
       
        if len(sentence) == sentence_length - len(header): #Check if expected sentence length is reached (minus header length)          
            sentence_complete = True 
            
            #Splitting the readout "sentence" based on character position (splitline)
            split_result = [sentence[i:j] for i, j in zip([0] + splitline, splitline + [None])]
            x_raw = split_result[0]
            y_raw = split_result[1]
            temp_raw = split_result[2]
  
            if int(x_raw[0]) == 1: #See inclimoneter reference documents for data conversion
                x = int(x_raw[1:6])/1000 * -1 
                #In summary, we check the first digit of each field for the sign (+/-) of the value 
                #then turn the remaining digits into a decimal value
                
            else: 
                x = int(x_raw[1:6])/1000
                
            if int(y_raw[0]) == 1:
                y = int(y_raw[1:6])/1000 * -1
            else:
                y = int(y_raw[1:6])/1000
                
            if int(temp_raw[0]) == 1:
                temp = round((int(temp_raw[1:6])/1000 * (9/5) + 32) * -1,7)
            else:
                temp = round((int(temp_raw[1:6])/1000 * (9/5) + 32),7)
        
        else:
            onebyte = ser.read().hex() #Reading bytes from serial port and adding to buffer                
            buf += onebyte 
            
            if reading_sentence: # if start bytes found on last pass...
                # start acculumlating the data 
                sentence += onebyte
            
            if header in buf: #Check if header has appeared. If so, begin generating a "sentence" of data        
                reading_sentence = True
                    
    return (x,y,temp)# temp

def ReadSentence_Mag(ser,header, splitline,sentence_length):
    """Converts serial transmission from magnetometer into readable values. 
    :param ser: serial.serial() serial port indicator
    :param header: string of header characters
    :param splitline: array of integers that indicate different values based on character location
    :param sentence_length: integer 
    """

    buf = ''
    sentence = ''
    
    reading_sentence = False
    sentence_complete = False
    
    while not sentence_complete: 
        
        if len(sentence) == sentence_length - len(header): #Check if expected sentence length is reached (minus header length)
            sentence_complete = True 
            
            #Splitting the readout "sentence" based on character position (splitline)
            split_result = [sentence[i:j] for i, j in zip([0] + splitline, splitline + [None])]          
            x_raw = split_result[0]
            y_raw = split_result[1]
            z_raw = split_result[2]
          
        else:
            
            bcmdtest = bytearray(('*99C').encode()) #Sending stream command to mag
            ser.write(bcmdtest)
            onebyte = ser.read().hex() #Reading bytes from serial port 
           
            if reading_sentence: # if start bytes found on last pass...    
                # start acculumlating the data 
                sentence += onebyte
         
            if header in onebyte: 
                
                reading_sentence = True
    
    return (round(s16(int(x_raw,16))*4/60000, 7), #Changing HEX to signed decimal from 2's complement..,,
            round(s16(int(y_raw,16))*4/60000, 7), #Then multiplying by scaling factor, and rounding.
            round(s16(int(z_raw,16))*4/60000,7)) #XYZ values are outputted from range of -30000 to 30000, must convert to -2 to 2 gauss
#     #return (x_raw,y_raw,z_raw)

    
    
