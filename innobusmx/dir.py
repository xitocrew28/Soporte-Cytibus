import os
import sys
import serial

path = "/dev"
listdir = os.listdir(path)

for file in listdir:
        if (file[0:6] == "ttyUSB"):
                print file
                s = serial.Serial("/dev/"+file,115200, timeout=1)
                s.flushInput()
                s.flushOutput()
                s.write("AT\r")
                st = s.readline()
                st = st + s.readline()
                st = st + s.readline()
                st = st + s.readline()
                s.close
                print st
                

