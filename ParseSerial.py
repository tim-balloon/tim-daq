import numpy as np
import serial 
import struct

def hexToFloat(value): #convert hexadecimal to floating point for x,y,z readings   
    return struct.unpack('!f', bytes.fromhex(value))[0]


def ParseSerial(ser, header, splitline, sentence_length, Nbytes):

    cnt = 0
    buf = ''
    sentence = ''

    sentenceread = False
    while cnt < Nbytes:
        onebyte = ser.read().hex() # to be safe, should set a timeout here, probably
        #print(onebyte,end='')
        buf += onebyte 

        if sentenceread: # if start bytes found on last pass
            # start acculumlating the data 
            sentence += onebyte

        if header in buf:
            if sentence != '' and len(sentence) == sentence_length:
                
                split_result = [sentence[i:j] for i, j in zip([0] + splitline, splitline + [None])]
                #print(split_result)
                print(int(split_result[7],16), # seq num
                      int(split_result[0],16), # x
                      int(split_result[1],16), # y
                      int(split_result[2],16), # x
                      int(split_result[6],16), # status
                      int(split_result[8],16)) # temperature
            sentenceread = True
            buf = ''
            sentence=''

        cnt += 1
        
    return

def ReadSentence(ser, header, splitline, sentence_length):

    buf = ''
    sentence = ''
    
    reading_sentence = False
    sentence_complete = False
    
    while not sentence_complete:
        
        
        
        if len(sentence) == sentence_length - len(header):
            
            sentence_complete = True        
            split_result = [sentence[i:j] for i, j in zip([0] + splitline, splitline + [None])]
            
            
        
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