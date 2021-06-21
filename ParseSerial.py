import numpy as np
import serial 
import struct
import time
def hexToFloat(value): #convert hexadecimal to floating point for gyro x,y,z readings   
    return struct.unpack('!f', bytes.fromhex(value))[0] 

def s16(value): #converts hex into signed decimal from 2's complement
    return -(value & 0x8000) | (value & 0x7fff) 

def cmd_ser(ser, cmdtext):
    
    # Needs carriage return
    bcmdtest = bytearray((cmdtext+'\r').encode())
    
    ser.write(bcmdtest)
    #time.sleep(0.01)
    if ser.in_waiting > 0:
        return ser.read().hex()
#     else:
#         print('Nothing returned')
        
# def ParseSerial(ser, header, splitline, sentence_length, Nbytes):

#     cnt = 0
#     buf = ''
#     sentence = ''

#     sentenceread = False
#     while cnt < Nbytes:
#         onebyte = ser.read().hex() # to be safe, should set a timeout here, probably
#         #print(onebyte,end='')
#         buf += onebyte 

#         if sentenceread: # if start bytes found on last pass
#             # start acculumlating the data 
#             sentence += onebyte

#         if header in buf:
#             if sentence != '' and len(sentence) == sentence_length:
                
#                 split_result = [sentence[i:j] for i, j in zip([0] + splitline, splitline + [None])]
#                 #print(split_result)
#                 print(int(split_result[7],16), # seq num
#                       int(split_result[0],16), # x
#                       int(split_result[1],16), # y
#                       int(split_result[2],16), # x
#                       int(split_result[6],16), # status
#                       int(split_result[8],16)) # temperature
#             sentenceread = True
#             buf = ''
#             sentence=''

#         cnt += 1
        
#     return

def ReadSentence_Gyro(ser, header, splitline, sentence_length):

    buf = ''
    sentence = ''
    
    reading_sentence = False
    sentence_complete = False
    
    while not sentence_complete:  
        if len(sentence) == sentence_length - len(header):            
            sentence_complete = True        
            split_result = [sentence[i:j] for i, j in zip([0] + splitline, splitline + [None])]
            #print(split_result)     
        else:
            onebyte = ser.read().hex() # to be safe, should set a timeout here, probably            
            buf += onebyte 
            
            if reading_sentence: # if start bytes found on last pass
                # start acculumlating the data 
                sentence += onebyte
                
            if header in buf:                
                reading_sentence = True
                       
    return (int(split_result[7],16), # seq numint(split_result[0],16), 
            hexToFloat(split_result[0]), # x
            hexToFloat(split_result[1]), # y
            hexToFloat(split_result[2]), # z
            int(split_result[6],16), # status
            int(split_result[8],16)) # temperature

def ReadSentence_Inclin(ser, header, splitline, sentence_length):
    buf = ''
    sentence = ''
    x = 0.0
    y = 0.0
    temp = 0.0
    reading_sentence = False
    sentence_complete = False
    
    while not sentence_complete:       
        if len(sentence) == sentence_length - len(header):
            
            sentence_complete = True 
            
            split_result = [sentence[i:j] for i, j in zip([0] + splitline, splitline + [None])]
            x_raw = split_result[0]
            y_raw = split_result[1]
            temp_raw = split_result[2]
            
            if int(x_raw[0]) == 1: #See inclimoneter reference documents for data conversion
                x = int(x_raw[1:6])/1000 * -1 
                #In summary, we check the first digit of each field for the sign of the value, then turn the remaining digits 
                #into a decimal value
                
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
            onebyte = ser.read().hex() # to be safe, should set a timeout here, probably           
            buf += onebyte 
            
            if reading_sentence: # if start bytes found on last pass
                # start acculumlating the data 
                sentence += onebyte
            
            if header in buf:
                
                reading_sentence = True
                    
    return (x,y,temp)# temp

def ReadSentence_Mag(ser,header, splitline,sentence_length):
    buf = ''
    sentence = ''
    
    reading_sentence = False
    sentence_complete = False
    
    while not sentence_complete:       
        if len(sentence) == sentence_length - len(header):
            sentence_complete = True 
        
            split_result = [sentence[i:j] for i, j in zip([0] + splitline, splitline + [None])]
            print(split_result)
            x_raw = split_result[0]
            y_raw = split_result[1]
            z_raw = split_result[2]
                
        else:
            bcmdtest = bytearray(('*99C\r').encode()) #Sending stream command to mag
            ser.write(bcmdtest)
            onebyte = ''
            
            #onebyte = cmd_ser(ser, '*99P')
            #print(ser.read().hex()) #Reading data stream
            onebyte = ser.read().hex()
            
            #print(onebyte)
            buf += onebyte 
            print(buf)
            if reading_sentence: # if start bytes found on last pass
                # start acculumlating the data 
                sentence += onebyte
                #print(sentence)
            
                
            if header in buf:             
                reading_sentence = True
    
    return (round(s16(int(x_raw,16))*4/60000, 7), #Changing HEX to signed decimal from 2's complement..,,
            round(s16(int(y_raw,16))*4/60000, 7), #Then multiplying by scaling factor, and rounding.
            round(s16(int(z_raw,16))*4/60000,7)) # XYZ values are outputted from range of -30000 to 30000, must convert to 
                                                    #-2 to 2 gauss
#     #return (x_raw,y_raw,z_raw)

    
    
