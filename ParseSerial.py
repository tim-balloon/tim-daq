import numpy as np
import serial 

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