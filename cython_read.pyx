import serial 
import struct
import time


cpdef double hexToFloat(value): #convert hexadecimal to floating point for gyro x,y,z readings   
    return struct.unpack('!f', bytes.fromhex(value))[0] 

cpdef double s16(value): #converts hex into signed decimal from 2's complement
    return -(value & 0x8000) | (value & 0x7fff) 

cpdef tuple ReadSentence_Gyro(ser, header, splitline, int sentence_length):
    
    
    cdef buf = ''
    cdef sentence = ''
    
    cdef bint reading_sentence = False
    cdef bint sentence_complete = False
    cdef int seq_num, status, temp
    cdef float x,y,z
    cdef int split_num = len(splitline)-1
    cdef list split_result = [None]*split_num
    cdef int i
    cdef double declaration_time = time.perf_counter()
    
    while not sentence_complete:  
        if len(sentence) == sentence_length - len(header):            
            sentence_complete = True     
            
            #split_result = [sentence[i:j] for i, j in zip([0] + splitline, splitline + [None])]
            for i in range(split_num):
                split_result[i] = sentence[splitline[i]:splitline[i+1]]              
            
            seq_num = int(split_result[7],16)
            x = hexToFloat(split_result[0])
            y = hexToFloat(split_result[1])
            z = hexToFloat(split_result[2])
            status = int(split_result[6],16)
            temp = int(split_result[8],16)
            
            #print(split_result)     
        else:
            onebyte = ser.read().hex() # to be safe, should set a timeout here, probably            
            buf += onebyte 
            
            if reading_sentence: # if start bytes found on last pass
                # start acculumlating the data 
                sentence += onebyte
                
                
            if header in buf:                
                reading_sentence = True
    
              
    return (seq_num, # seq numint(split_result[0],16), 
            x, # x
            y, # y
            z, # z
            status, # status
            temp) # temperature
#     return (int(split_result[7],16), # seq numint(split_result[0],16), 
#             hexToFloat(split_result[0]), # x
#             hexToFloat(split_result[1]), # y
#             hexToFloat(split_result[2]), # z
#             int(split_result[6],16), # status
#             int(split_result[8],16)) # temperature

cpdef tuple ReadSentence_Inclin(ser, header, list splitline, int sentence_length):
    buf = ''
    sentence = ''
    cdef float x = 0.0
    cdef float y = 0.0
    cdef float temp = 0.0
    
    cdef bint reading_sentence = False
    cdef bint sentence_complete = False
    
    cdef int split_num = len(splitline)-1
    cdef list split_result = [None]*split_num
    cdef int i
    
    while not sentence_complete:       
        if len(sentence) == sentence_length - len(header):
            
            sentence_complete = True 
            
            #split_result = [sentence[i:j] for i, j in zip([0] + splitline, splitline + [None])]
            for i in range(split_num):
                split_result[i] = sentence[splitline[i]:splitline[i+1]]     
            
            x_raw = split_result[0]
            y_raw = split_result[1]
            temp_raw = split_result[2]
            print(split_result)
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

cpdef tuple ReadSentence_Mag(ser,header, list splitline, int sentence_length):
    buf = ''
    sentence = ''
    
    cdef bint reading_sentence = False
    cdef bint sentence_complete = False
    cdef double x, y, z
    
    cdef int split_num = len(splitline)-1
    cdef list split_result = [None]*split_num
    cdef int i
    
    while not sentence_complete: 
        
        if len(sentence) == sentence_length - len(header):
            sentence_complete = True 
        
            #split_result = [sentence[i:j] for i, j in zip([0] + splitline, splitline + [None])]
            for i in range(split_num):
                split_result[i] = sentence[splitline[i]:splitline[i+1]]     
            #rint(split_result)
            
            x = round(s16(int(split_result[0],16))*4/60000, 7)
            y = round(s16(int(split_result[1],16))*4/60000, 7)
            z = round(s16(int(split_result[2],16))*4/60000,7)
                
        else:
            bcmdtest = bytearray(('*99C').encode()) #Sending stream command to mag
            ser.write(bcmdtest)
            onebyte = ''
            
            #onebyte = cmd_ser(ser, '*99P')
            #print(ser.read().hex()) #Reading data stream
            onebyte = ser.read().hex()
            buf += onebyte 
            #print(onebyte)
            
            #print(buf)
            if reading_sentence: # if start bytes found on last pass
                
                # start acculumlating the data 
                sentence += onebyte
                #print(sentence)
            
                
            if header in onebyte: 
                
                reading_sentence = True
    
    return (x, #Changing HEX to signed decimal from 2's complement..,,
            y, #Then multiplying by scaling factor, and rounding.
            z) # XYZ values are outputted from range of -30000 to 30000, must convert to 
                                       