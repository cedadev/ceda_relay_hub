#Script to analyse concatenated output from get_all_LCD.py and calculate average delay for each string

import sys
import os

import pandas as pd
#from datetime.datetime import timedelta

lcd_file = sys.argv[1]

with open(lcd_file, 'r') as f:
    lines = [i.rstrip() for i in f.readlines()]

#print (f"{len(lines)}")

#automatically detect synchroniser names
streams = {}
for line in lines:
    
    for i in line.split(','):

        #get producers
        if 'producer' in i:
            producer = i.lstrip().split(' ')[0]

            if producer not in streams.keys():
                streams[producer] = []
        
            (streams[producer]).append(pd.Timedelta(i.lstrip().split(' ')[1]))

print ('here')       

    
    
    #if 'Label:' in line:
     #   if line.split(" ")[1] not in syncs:
      #      syncs.append(line.split(" ")[1])