#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import serial
from PyQt4 import QtCore
import os
import RPi.GPIO as GPIO
#from ClMifare import clMifare


class clSerial(QtCore.QThread):
    sPort = ''
    sPort3G = ''     
    velocidad = 112500
    
    def __init__(self, parent, clDB):
        self.clDB = clDB
        self.parent = parent
        QtCore.QThread.__init__(self)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(18,GPIO.OUT)
        self.setupSerial()

    def setupSerial(self):
        print "DOWN"
        GPIO.output(18,False)
        time.sleep(1)
        print "UP"
        GPIO.output(18,True)
        time.sleep(10)
        path = "/dev"
        print '###             Buscando Puertos          ###'
        error = 0
        self.sPort = ''
        self.sPort3G = ''
        self.parent.flRFID = False
        self.parent.iComm = 0
        while (self.sPort == '' or self.sPort3G == ''):
            self.sPort = ''
            self.sPort3G = ''
            listdir = os.listdir(path)
            for file in listdir:
                if (file[0:6] == "ttyUSB"):
                    print "/dev/"+file
                    try:
                        s = serial.Serial("/dev/"+file, self.velocidad, timeout=1)
                        time.sleep(4)
                        s.flushInput()
                        s.flushOutput()
                        s.write(b's')
                        st = s.readline()
                        #print "serial: ",st," len: ",len(st)
                        if (len(st) == 12) and (st.find("Ix") != -1):
                            self.parent.serialNumber = st
                            self.sPort = "/dev/"+file
                            s.write(b'v')
                            self.parent.version = s.readline()
                            #print "version: "+self.parent.version

                        if (st == ""):
                            #print "modem"
                            s.flushInput()
                            s.flushOutput()
                            i = 0
                            while ((st.find("OK") == -1) and (i < 20)):
                                s.write("+++\r\x1A\r\ATE0\r")
                                st += s.readline()
                                i += 1
                                #print str(i)+"st "+st
                            #print "while"
                            if (st.find("OK") != -1):
                                self.sPort3G = "/dev/"+file
                        s.flushInput()
                        s.flushOutput()
                        s.close
                    except:
                        if (error == 0):
                            print '###                             USB Unabled  ###'
                            error = 1
            #if (self.sPort == '' and self.sPort3G == ''):
            #    print "DOWN"
            #    GPIO.output(18,False)
            #    time.sleep(1)
            #    print "UP"
            #    GPIO.output(18,True)
            #    time.sleep(10)

                
                



        self.parent.serialNumber = self.parent.serialNumber.split("\r\n")[0]
        self.parent.version = self.parent.version.split("\r\n")[0]
        self.parent.flRFID = True
        print "RFID: " + self.sPort
        print "3G: " + self.sPort3G
        #print "SN ",self.parent.serialNumber
        #print "ver ",self.parent.version
        self.signal = QtCore.SIGNAL("signal")
        self.signal2 = QtCore.SIGNAL("signal2")
        self.parent.lblNS.setText("NS:"+self.parent.serialNumber)
        self.parent.lblNSFirmware.setText(self.parent.version)

        #print "init RFID:",self.parent.flRFID
    '''
    def run(self):

        self.preaderLocal = self.initSerial()
        clmifare = clMifare(self.parent, self.preaderLocal,self.clDB)
        while(True):
##            self.preaderLocal = self.parent.initSerial()
            print '     Siempre leyendo aca'
            self.out = ''
            print '#############################'
            self.out = self.preaderLocal.readline()
            ok = clmifare.cobrar(self.out)
##            self.preaderLocal.close()
            print 'Respuesta del cobro', ok
            senial = self.emit(self.signal, ok)
            print 'Termine la primer senial'
            #el sleep de tres es para la Pi
            #time.sleep(3)
            #time.sleep1)
            #time.sleep(8)
            self.emit(self.signal2)
            print 'Termine la segunda senial'
##            self.preaderLocal = self.parent.initSerial()
            print '#############################'
    '''
    
    def initSerial(self):
      try:
        print '###                Iniciando Puerto Serie ###'
        self.ser = serial.Serial(self.sPort, self.velocidad)
        self.ser.flushInput()
        self.ser.flushOutput()
        return self.ser
      except:
        return None
    
    def init3G(self):
      try:
        #print '###                    Iniciando Modem 3G ###'
        self.ser3G = serial.Serial(self.sPort3G, self.velocidad, timeout = 1)
        self.ser3G.flushInput()
        self.ser3G.flushOutput()
        return self.ser3G
      except:
        return None

    def initSerialEsperandoOK(self):
        print '*******************************Iniciando puerto esperando el OK'
        self.ser = serial.Serial(self.sPort, self.velocidad, timeout = 1)
        self.ser.flushInput()
        self.ser.flushOutput()
        return self.ser

    def closeSerial(self):
        print '****************************************Cerrando el puerto RDIF'
        self.ser.close()

    def close3G(self):
        print '****************************************Cerrando Modem 3G'
        self.ser3G.close()


