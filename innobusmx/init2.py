#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtGui
from PyQt4 import QtCore
import serial
import sqlite3
import os
from time import strftime
import time
import threading
import subprocess
from datetime import datetime
import urllib
from PyQt4 import QtCore as qtcore
from curses import ascii
import base64
import re

    ##################################################
    # INICIA CODIGO AGREGADO POR RENE DELGADO        #
    # FECHA: 12 DE SEP 2017                          #
    # PROPOSITO: EVITAR QUE EL SCRIT SE TERMINE      #
    #            CON ERROR CUANDO EXISTA UN PROBLEMA #
    #            AL TRASMITIR POR EL PUERTO SERIE.   #   
    ##################################################
#Comienza declaracion de variables globales
portName_3G = ""
portName_RFID = ""
portSpeed = 115200
lastPositionGPS = ""
lastLatitudGPS = ""
lastLongitudGPS = ""
lastVelocidadGPS = ""
statusPositionGPS = "NONE"
SYC_TCP_Time = False
SYSTEM_CONFIGURATIONS_SQL = False
IdTransportista = ""
IdUnidad = ""
TCP_ShellIsOpen  = False
CTRL_Z_Sended = False
TCP_ServerRunning = False
GPS_Connection = False
USB_Disconect = False
USB_Disconect_LastTime = ""
GPS_Send_Index = 1
GPRS_NoReg = False
GPRS_NoReg_LastTime = ""
GPRS_NoPDP = False
GPRS_NoPDP_LastTime = ""
Quetel_Reset = False
Quetel_Reset_LastTime = False


class clsSerial():

    def readCommand(self,Command,TimeOut,Answer,Attemps):
        global portName_3G
        global portName_RFID
        global portSpeed
        self.inWaiting = 0
        self.path = "/dev"
        self.InitTime = 0
        self.EndTime = 0
        self.buff = ""
        self.ErrorNumber = 0
        self.AnswerFind  = 0
        olSerial = clsSerial()
        
        print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
        print "We look for: " + str(Answer)
        for i in range (Attemps):
            if portName_3G == "" or portName_RFID == "":
          
                olSerial.DefinePort()
            else:
               
                try:
                    self.SerialPortX = serial.Serial("/dev/"+portName_3G,portSpeed, timeout=1) 
                except:
                    self.ErrorNumber = 1
                    print "Error: serial.Serial"
                try:
                    self.SerialPortX.flushInput()
                except:
                    self.ErrorNumber = 2
                    print "self.SerialPortX.flushInput"
                try:
                    self.SerialPortX.flushOutput()
                except:
                    self.ErrorNumber = 3
                    print "self.SerialPortX.flushOutput"
                try:
                    self.buff = ""
                    self.SerialPortX.write(Command)
                    self.ErrorNumber = 0
                    self.InitTime = time.time()

                    print time.ctime()+ " (TX, " + str(TimeOut)+ "Sec.)>> " + Command 
                except:
                    self.ErrorNumber = 4
                    print "Error: SerialPortX.write."
             
                while ((time.time() - self.InitTime) < TimeOut):

                    try:
                        self.inWaiting = self.SerialPortX.inWaiting()
                    except:
                        self.ErrorNumber = 5
                        print "Error: SerialPortX.inWaiting."
                    if self.inWaiting > 0:
                        try:
                            self.buff += self.SerialPortX.read(self.inWaiting)
                        except:
                            self.ErrorNumber = 6
                            print "Error: SerialPortX.read."
                            
                    if self.ErrorNumber!=0:
                        break
                    for  j in Answer:
               
                        if ( self.buff.find(j)!= -1):
                            print "Find: " + j
                            self.AnswerFind = 1
                            break
                    if self.AnswerFind == 1:
                        break
                    time.sleep(1)
                if (self.ErrorNumber> 0):
                    portName_3G = ""
                    portName_RFID = ""

                print time.ctime()+ " (RX)<< "
                print self.buff
                
                if self.AnswerFind == 1:
                    print "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
                    return self.buff
                
        print "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
        return self.buff
        
    
    def DefinePort(self):
        global portName_3G
        global portName_RFID
        global portSpeed
        global USB_Disconect
        global USB_Disconect_LastTime
        self.inWaiting = 0
        self.port1 = ""
        self.port2 = ""
        self.countPorts = 0
        self.path = "/dev"
        self.InitTime = 0
        self.EndTime = 0
        self.buff = ""
        self.ErrorNumber = 0
        self.portAux = ""
        self.AnswerRecived = True
        self.DefinedPort = False
        listdir = os.listdir(self.path)
        for Attemps in range (4):
            if self.DefinedPort:
                break
            print  "Buscando puertos USB... "
            USB_Disconect = True
            USB_Disconect_LastTime = time.strftime('%d%b%Y_%H%M%S')
            for file in listdir:
                if (file.find("ttyUSB") != -1):
                    print file
                    self.countPorts = self.countPorts + 1
                    if (self.countPorts == 1):
                        self.port1 = file
                    else:
                        self.port2 = file
            if (self.countPorts < 2):
                print  "Puertos insuficientes!"

                time.sleep(3)
            else:
                for port in range(1,3) :
                    try:
                        if port  == 1:
                            self.portAux = self.port1
                        if port  == 2:
                            self.portAux= self.port2
                        print "Identificando: " + self.portAux
                        self.SerialPortX = serial.Serial("/dev/"+self.portAux,portSpeed, timeout=1) 
                    except:
                        self.ErrorNumber = 1
                        print "Error: serial.Serial"
                    try:
                        self.SerialPortX.flushInput()
                    except:
                        self.ErrorNumber = 2
                        print "self.SerialPortX.flushInput"
                    try:
                        self.SerialPortX.flushOutput()
                    except:
                        self.ErrorNumber = 3
                        print "self.SerialPortX.flushOutput"
                    try:
                        self.buff = ""
                        if not self.AnswerRecived:
                            self.SerialPortX.write("\x1A")
                            self.InitTime = time.time()
                            print time.ctime()+ " (TX)>> " + "\x1A"

                        self.SerialPortX.write("ATE0\r")
                        self.InitTime = time.time()
                        print time.ctime()+ " (TX, 5Sec.)>> " + "ATE0\r"
                    except:
                        self.ErrorNumber = 4
                        print "Error: SerialPortX.write."          
                    while ((time.time() - self.InitTime) < 5):
                        try:
                            self.inWaiting = self.SerialPortX.inWaiting()
                           
                        except:
                            self.ErrorNumber = 5
                            print "Error: SerialPortX.inWaiting."
                        if self.inWaiting > 0:
                            try:
                                self.buff += self.SerialPortX.read(self.inWaiting)    
                            except:
                                self.ErrorNumber = 6
                                print "Error: SerialPortX.read."
                        if self.ErrorNumber !=0:
                            break
                        if ( self.buff.find("OK\r")!= -1):
                            break
                        time.sleep(1)

                    print time.ctime()+ " (RX)<< "
                    print self.buff
                    
                    if ((self.buff.find("OK\r")!= -1)and (len(self.buff) == 6)) or (self.buff.find("ATE0\r")!= -1) or (self.buff.find("SEND OK")!= -1) or (self.buff.find("ERROR")!= -1)  or (self.buff.find("NO CARRIER")!= -1) :
                       portName_3G = self.portAux
                       if port == 1:
                           portName_RFID = self.port2
                       else:
                           portName_RFID = self.port1
                       self.DefinedPort = True
                    else:
                        portName_3G = ""
                        portName_RFID = ""
                    if port == 2:
                        if portName_3G == "" and portName_RFID == "":
                            self.AnswerRecived = False
                    try:
                        self.SerialPortX.flush()
                    except:
                        self.ErrorNumber = 7
                        print "Error: SerialPortX.flush."
                    if self.ErrorNumber > 0:
                        time.sleep(1)
                        portName_3G  = ""
                        portName_RFID = ""
                      

        print "portName_3G: " + portName_3G
        print "portName_RFID: " + portName_RFID
        print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
        if self.DefinedPort:
            print "DEFINE PORT Succesfully!"
        else:
            print "DEFINE PORT Fail!"
        print "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"    
                
     
    
  
class clsQuectel ():
    def Restart(self):
        self.oSerial = clsSerial()
        self.AnswerLen  = 0
        self.TuplaOfAnswers = ("RDY","RDY")
        self.SerialAnswer = self.oSerial.readCommand("+++",15,self.TuplaOfAnswers,5)
        self.TuplaOfAnswers = ("RDY","RDY")
        self.SerialAnswer = self.oSerial.readCommand("AT+QRST=1,0\r",60,self.TuplaOfAnswers,5)
        self.TuplaOfAnswers = ("OK","ATE0")
        self.SerialAnswer = self.oSerial.readCommand("ATE0\r",60,self.TuplaOfAnswers,5)

    def TCP_Configuration (self,Attemps):
        global TCP_ShellIsOpen
        global CTRL_Z_Sended
        global TCP_ServerStatus
        global TCP_ServerRunning
       
        self.statusTCP = 0
        self.oSerial = clsSerial()
        self.oQuectel  = clsQuectel()
        self.PORT = "11000"
        self.SERVER = "\"innovaslp.dyndns.org\""
        self.TuplaOfAnswers = ("OK\r","OK\r")
        self.SerialAnswer = self.oSerial.readCommand("AT+CMGF=1\r" ,15,self.TuplaOfAnswers,3)         
        for T in range (Attemps):
            global SYC_TCP_Time
            self.TuplaOfAnswers = ("CONNECT","+QIOPEN")
            self.SerialAnswer = self.oSerial.readCommand("AT+QIOPEN=1,0,\"TCP\"," + self.SERVER + "," + self.PORT + ",0,0\r" ,45,self.TuplaOfAnswers,3)
            if (self.SerialAnswer.find("CONNECT") != -1) or (self.SerialAnswer.find("+QIOPEN: 0,0") != -1) or (self.SerialAnswer.find("+QIOPEN: 0,562")!= -1):
                self.TuplaOfAnswers = ("OK\r","OK\r")
                self.SerialAnswer = self.oSerial.readCommand("AT+QISTATE=1,0\r" ,15,self.TuplaOfAnswers,3)
                TCP_ServerRunning = True
                self.statusTCP = 1
            if (self.SerialAnswer.find("+QIOPEN: 0,552")!= -1):
                TCP_ServerRunning = False

   
            if self.statusTCP == 1:
                self.TuplaOfAnswers = ("OK\r","ERROR",">")
                TCP_ShellIsOpen = True
                self.SerialAnswer = self.oSerial.readCommand("AT+QISEND=0\r" ,15,self.TuplaOfAnswers,3)
                if self.SerialAnswer.find(">")!= -1:
                    CTRL_Z_Sended = False
                    if not SYC_TCP_Time:
                       if self.oQuectel.SYC_TCP_Time():
                            CTRL_Z_Sended = True                        
                            break
                    if self.oQuectel.SEND_Position_BY_TCP():
                        CTRL_Z_Sended = True                      
                        break
                elif self.SerialAnswer.find("ERROR")!= -1:
                     break

                    
        print "Statues TCP " + str(TCP_ServerRunning)   
        self.oQuectel.TCP_Close_Shell()




    def TCP_Close_Shell (self):
        global CTRL_Z_Sended
        self.StatusTCPClose = False 
        self.oSerial = clsSerial()        

        if not CTRL_Z_Sended:
            if not CTRL_Z_Sended:
                for T in range(3):
                    self.TuplaOfAnswers = ("SEND","OK")#Nada que buscar solo aseguramos que se envie "\x1A"
                    self.SerialAnswer = self.oSerial.readCommand("\x1A" ,3,self.TuplaOfAnswers,1)
                    self.TuplaOfAnswers = ("QISEND","OK","ERROR")
                    self.SerialAnswer = self.oSerial.readCommand("AT+QISEND=0,0\r" ,15,self.TuplaOfAnswers,1)
                    if self.SerialAnswer.find("QISEND") != -1 or self.SerialAnswer.find("ERROR") != -1:
                        self.CTRL_Z_Sended = True
                        break
                    
        #****************************************************************************************************
        #****************************************************************************************************
        #Inicia c[odigo modificado por Abel M. 21            
        self.TuplaOfAnswers = ("OK\r","ERROR",">")
        self.SerialAnswer = self.oSerial.readCommand("AT+QISEND=0\r" ,5,self.TuplaOfAnswers,1)
        if self.SerialAnswer.find(">")!= -1:
            self.oSerial = clsSerial()
            self.TuplaOfAnswers = ("close", "CLOSE")
            self.SerialAnswer = self.oSerial.readCommand("quit\r\x1A\r" ,5,self.TuplaOfAnswers,1)
            if (self.SerialAnswer.find("close")!= -1) or (self.SerialAnswer.find("CLOSE")!= -1):
                print "Encontre close"
                self.oSerial = clsSerial()

        self.TuplaOfAnswers = ("OK","OK")
        self.SerialAnswer = self.oSerial.readCommand("AT+QICLOSE=0\r",15,self.TuplaOfAnswers,2)
        if self.SerialAnswer.find("OK") != -1:
            self.StatusTCPClose = True
            
        if self.StatusTCPClose:
            print "TCP CLOSE Succsesfully!"
            #self.TuplaOfAnswers = ("OK\r","OK\r")
            #self.SerialAnswer = self.oSerial.readCommand("AT+QIDEACT=1\r",15,self.TuplaOfAnswers,2)
            #if self.SerialAnswer.find("OK") != -1:
            return True
        else:
            print "TCP CLOSE Fail!"
            #self.TuplaOfAnswers = ("OK\r","OK\r")
            #self.SerialAnswer = self.oSerial.readCommand("AT+QIDEACT=1\r",15,self.TuplaOfAnswers,2)
            #if self.SerialAnswer.find("OK") != -1:
            return False
        #****************************************************************************************************
        #****************************************************************************************************

        
    def SEND_Position_BY_TCP (self):
        #El formato de la trama que se enviara esta separado por ","Comas, debe incluid final de cadena \r utilizar la fucnion trama.encode() y concatenarle (<crtl+z> "\x1A")
        #Sintaxis Trama: TipoDeOperacion,idTransportista,idUnidad,FehaHoraUTM,Latitud,Longitud,Velocidad,ConsecutivoArrancaCuandoIniciaConElScriptEn1
        global TIME_SEND_LAST_POSITION
        global lastLatitudGPS
        global lastLongitudGPS
        global lastVelocidadGPS
        global statusPositionGPS
        global SYC_TCP_Time
        global SYSTEM_CONFIGURATIONS_SQL
        global IdTransportista
        global IdUnidad
        global GPS_Send_Index
        self.SendPositionSuccesfully = False
        self.DateTimeRPI  = ""
        self.Trama = ""
        self.oSerial = clsSerial()
        
        if SYC_TCP_Time and SYSTEM_CONFIGURATIONS_SQL:
            self.DateTimeRPI = time.strftime('%d-%m-%Y %H:%M:%S')
            
            self.Trama = "1,"+ IdTransportista + "," + IdUnidad + "," + self.DateTimeRPI  + "," +lastLatitudGPS[:-1]+ "," + lastLongitudGPS[:-1]  + "," + lastVelocidadGPS + "," +str(GPS_Send_Index) + "\r"
            #self.Trama = "1,1,5,22-09-2017 18:12:13,22.139857,-101.033012,0.0,53\r"
            #2840.8368
      
            self.TuplaOfAnswers = ("recv","ERROR","closed")
            self.SerialAnswer = self.oSerial.readCommand( self.Trama.encode() + "\x1A",15,self.TuplaOfAnswers,3)
            if self.SerialAnswer.find("recv")!= -1:
                self.TuplaOfAnswers = ("OK\r",">")
                self.SerialAnswer = self.oSerial.readCommand("AT+QIRD=0,1500\r" ,20,self.TuplaOfAnswers,5)

                #print "self.SerialAnswer:-",self.SerialAnswer,"-",str(len(self.SerialAnswer)),">>",self.SerialAnswer.find("+QIRD: 1\r1") 
         
                if ((self.SerialAnswer.find("@")!= -1)  and (len(self.SerialAnswer)== 34)) or (self.SerialAnswer.find("+QIRD: 1\r") != -1):
                    self.SendPositionSuccesfully = True
                  
        if self.SendPositionSuccesfully:
            print "SEND POSITION BY TCP Succesfully!"
            GPS_Send_Index += 1
            return True
        else:
            print "SEND POSITION BY TCP Fail!"
            return False
            



    def HTTP_Post(self):
        global TIME_SEND_LAST_POSITION
        global lastLatitudGPS
        global lastLongitudGPS
        global lastVelocidadGPS
        global statusPositionGPS
        global SYC_TCP_Time
        global SYSTEM_CONFIGURATIONS_SQL
        global IdTransportista
        global IdUnidad
        global TCP_ServerRunning
        global GPS_Connection
        global USB_Disconect
        global USB_Disconect_LastTime
        global GPS_Send_Index
        global GPRS_NoReg 
        global GPRS_NoReg_LastTime
        global GPRS_NoPDP 
        global GPRS_NoPDP_LastTime
        global Quetel_Reset 
        global Quetel_Reset_LastTime
        self.URL = "http://www.ingmulti.com/Innobus/insert.php?"
        self.URL_Length = ""
        self.statusPostHttp  = False
        self.Unidad = "Unidad="
        self.Comentarios = ""
        self.Trama = "Trama="         

        self.DateTimeRPI = time.strftime('%d_%m_%Y_%H_%M_%S')
        self.Unidad += IdUnidad + "&"
        self.Trama += "1,"+ IdTransportista + "," + IdUnidad + "," + self.DateTimeRPI  + "," +lastLatitudGPS[:-1]+ "," + lastLongitudGPS[:-1]  + "," + lastVelocidadGPS + "," + str(GPS_Send_Index) + "&"
        self.URL += self.Trama

        if Quetel_Reset:
            self.Comentarios += ",Q_RST_" + Quetel_Reset_LastTime
        if GPRS_NoPDP:
            self.Comentarios += ",NO_PDP_" + GPRS_NoPDP_LastTime
        if GPRS_NoReg:
            self.Comentarios += ",NO_REG_" + GPRS_NoReg_LastTime
        if USB_Disconect:
            self.Comentarios += ",NO_USB_" + USB_Disconect_LastTime
        if not GPS_Connection:
            self.Comentarios += ",NOT_GPS"
        if not TCP_ServerRunning:
             self.Comentarios += ",TCP_DOWN"
        if not SYC_TCP_Time:
             self.Comentarios += ",NOT_SYC"
        if not SYSTEM_CONFIGURATIONS_SQL:
             self.Comentarios += ",NOT_SQL"


        
        self.Comentarios = "Comentarios="  + self.Comentarios [1:] 
   
        self.URL  += self.Unidad + self.Trama + self.Comentarios

            
            
        self.URL_Length = str(len(self.URL))
        self.TuplaOfAnswers = ("OK","CONNECT")
        self.SerialAnswer = self.oSerial.readCommand("AT+QHTTPURL=" + self.URL_Length + ",80\r",20,self.TuplaOfAnswers,5)
        self.TuplaOfAnswers = ("OK","OK")
        self.SerialAnswer = self.oSerial.readCommand(self.URL,20,self.TuplaOfAnswers,5)
        self.TuplaOfAnswers = ("OK","CONNECT")
        self.SerialAnswer = self.oSerial.readCommand("AT+QHTTPPOST=1,80,80\r",20,self.TuplaOfAnswers,5)
        self.TuplaOfAnswers = ("+QHTTPPOST","+QHTTPPOST")
        self.SerialAnswer = self.oSerial.readCommand("\r",30,self.TuplaOfAnswers,5)
        if self.SerialAnswer.find("0,200,17") != -1 or self.SerialAnswer.find("0,200,16") != -1:
            self.statusPostHttp  = True

        if self.statusPostHttp:
            print "HTTP POST Succesfully!"
            USB_Disconect  = False
            GPRS_NoPDP = False
            GPRS_NoReg = False
            Quetel_Reset = False
        else:
            print "HTTP POST Fail!"
                
                
         
         

        
        
    def SYC_TCP_Time(self):
        global SYC_TCP_Time
        self.DateTcpServer = ""
        self.TimeTcpServer = ""
        self.statusSYC = 0
        self.oSerial = clsSerial()
        SYC_TCP_Time = False
        self.TuplaOfAnswers = ("recv","ERROR")
        self.SerialAnswer = self.oSerial.readCommand("00\r\x1A\r",15,self.TuplaOfAnswers,1)
        if self.SerialAnswer.find("recv")!= -1:
            self.TuplaOfAnswers = ("OK\r",">")
            self.SerialAnswer = self.oSerial.readCommand("AT+QIRD=0,1500\r" ,20,self.TuplaOfAnswers,5)
            if (self.SerialAnswer.find("-")!= -1) and (self.SerialAnswer.find(":")!= -1) and (self.SerialAnswer.find("OK")!= -1) and (len(self.SerialAnswer)== 40):
                      self.TuplaDateTime = self.SerialAnswer.split(" ")
                      self.DateTcpServer = self.SerialAnswer[13:-17]
                      self.TimeTcpServer = self.SerialAnswer[24:-8]
                      self.DateTime = "\""+self.DateTcpServer +" "+str(self.TimeTcpServer)+"\""  
                      self.command = "sudo date -s \""+self.DateTcpServer +" "+self.TimeTcpServer+"\""
                      if os.system(self.command) == 0:
                          SYC_TCP_Time = True
              
                      
        if SYC_TCP_Time:
            print "SYC TCP TIME Succesfully!"
            return True
        else:
            print "SYC TCP TIME Fail!"
            return False
        

      
        
    
    def PDP_Configuration (self,Attemps):
        global GPRS_NoPDP 
        global GPRS_NoPDP_LastTime 
        self.statusPDP = 0
        self.oSerial = clsSerial()
        self.APN  = "\"internet.itelcel.com\""
        #self.APN  = "\"wwwcorps.itelcel.com\""
        self.USER = "\"webgprs\""
        self.PASSWORD = "\"webgprs2002\""
        for P in range (Attemps):
            self.TuplaOfAnswers = ("OK\r","OK\r")
            self.SerialAnswer = self.oSerial.readCommand("AT+QHTTPCFG=\"contextid\",1\r",15,self.TuplaOfAnswers,3)
            if self.SerialAnswer.find("OK") != -1:
                self.statusPDP = 1
                break
        for P in range (Attemps):
            self.TuplaOfAnswers = ("OK\r","e\r")
            self.SerialAnswer = self.oSerial.readCommand("AT+QIACT?\r",15,self.TuplaOfAnswers,3)
            if (self.SerialAnswer.find("+QIACT") != -1) and  (self.SerialAnswer.find("1,1,1") != -1) and  (self.SerialAnswer.find(".") != -1):
                self.statusPDP = 11111
                break
            elif self.SerialAnswer.find("OK") != -1:
                self.statusPDP += 10
                break
        if self.statusPDP != 11111:
            for P in range (Attemps):
                self.TuplaOfAnswers = ("OK\r","OK\r")
                self.SerialAnswer = self.oSerial.readCommand("AT+QICSGP=1,1,"+ self.APN + "," + self.USER + "," + self.PASSWORD + ",1\r" ,15,self.TuplaOfAnswers,3)
                if self.SerialAnswer.find("OK") != -1:
                    self.statusPDP += 100
                    break
            for P in range (Attemps):
                self.TuplaOfAnswers = ("OK\r","OK\r")
                self.SerialAnswer = self.oSerial.readCommand("AT+QIACT=1\r",15,self.TuplaOfAnswers,3)
                if self.SerialAnswer.find("OK") != -1:
                    self.statusPDP += 1000
                    break
            for P in range (Attemps):
                self.TuplaOfAnswers = ("OK\r","OK\r")
                self.SerialAnswer = self.oSerial.readCommand("AT+QIACT?\r",15,self.TuplaOfAnswers,3)
                if self.SerialAnswer.find("+QIACT") != -1:
                   self.statusPDP += 10000
                   break
        
        if self.statusPDP == 11111:
            print "PDP Configuration Succesfully!"
          
    
            return True
        else:
            print "PDP Configuration Fail!"
            GPRS_NoPDP_LastTime  = time.strftime('%d%b%Y_%H%M%S')
            GPRS_NoPDP = True
            return False
        
    def TresG_Connection(self,Attemps):
        global GPRS_NoReg 
        global GPRS_NoReg_LastTime 
        self.statusConnection = 0
        self.oSerial = clsSerial()

    
        for T in range (Attemps):
            self.TuplaOfAnswers = ("+CPIN: READY","+CME ERROR","OK\r")
            self.SerialAnswer = self.oSerial.readCommand("AT+CPIN?\r",8,self.TuplaOfAnswers,3)
            if self.SerialAnswer.find("+CPIN: READY") != -1:
                self.statusConnection  = 1
                break
        for T in range (Attemps):
            self.TuplaOfAnswers = ("OK\r","OK\r")
            self.SerialAnswer = self.oSerial.readCommand("AT+CSQ\r",5,self.TuplaOfAnswers,3)
            if len(self.SerialAnswer) > 11:
                try:
                    if int(self.SerialAnswer[8:-11]) > 5 and int(self.SerialAnswer[8:-11]) != 99:
                        self.statusConnection  += 10
                        break
                except:
                    print "Error: Casting int() SignalQuality."
            
        for T in range (Attemps):
            self.TuplaOfAnswers = ("OK\r","OK\r")
            self.SerialAnswer = self.oSerial.readCommand("AT+CREG?\r",5,self.TuplaOfAnswers,3)
            if self.SerialAnswer.find("+CREG: 0,1") != -1:
                self.statusConnection  += 100
                break
        if self.statusConnection == 111:
            print "NETWORK Connection Succesfully!"
        
            return True
        else:
            print "NETWORK Connection Fail!"
            GPRS_NoReg_LastTime = time.strftime('%d%b%Y_%H%M%S')
            GPRS_NoReg = True
            
            return False
   
        
        
    
    def GPS_Connection(self,Attemps):
        global lastPositionGPS
        global lastLatitudGPS 
        global lastLongitudGPS 
        global lastVelocidadGPS 
        global statusPositionGPS
        global GPS_Connection
        self.SerialAnswer = ""
        self.oSerial = clsSerial()

        for g in range (Attemps):
            self.TuplaOfAnswers = ("+QGPS: 0","+QGPS: 1","OK\r")
            self.SerialAnswer = self.oSerial.readCommand("AT+QGPS?\r",15,self.TuplaOfAnswers,3)
            if self.SerialAnswer.find("+QGPS: 1") != -1:
                 self.TuplaOfAnswers =("OK","OK\r")
                 self.SerialAnswer = self.oSerial.readCommand("AT+QGPSLOC=0\r",10,self.TuplaOfAnswers,3)
                 self.AnswerLen = len(self.SerialAnswer)
                 if (self.AnswerLen > 50) and (self.SerialAnswer[:11].find("+QGPSLOC:")!= -1)and( self.SerialAnswer[-4:-2].find("OK")!= -1 ):
                     lastPositionGPS = self.SerialAnswer[12:-8]
                     tuplaPosition = lastPositionGPS.split(",")
                     lastLatitudGPS = tuplaPosition [1]
                     lastLongitudGPS = tuplaPosition [2]
                     lastVelocidadGPS = tuplaPosition [7]
                     statusPositionGPS = "ACTUAL"
                     GPS_Connection = True
                     return  True
                    
            else:
                self.TuplaOfAnswers = ("AT+QGPS=1","+CME ERROR: 504")
                self.SerialAnswer = self.oSerial.readCommand("AT+QGPS=1\r",15,self.TuplaOfAnswers,3)
        statusPositionGPS = "OLD"
        GPS_Connection = False
        return False
    
    def Detect_Reset_With_ATE0(self):
        #Esta funcion sirve para detectar si se encendio el ECO una vez iniciado el Script
        #lo cual nos indica que el Quectel se reinicio durante la ejecucion del Scrip.
        global Quetel_Reset 
        global Quetel_Reset_LastTime
        self.ResetInLastCycle = False
        
        self.TuplaOfAnswers = ("OK\r","OK\r")
        self.SerialAnswer = self.oSerial.readCommand("ATE0\r" ,4,self.TuplaOfAnswers,2)

        if  self.SerialAnswer.find("ATE0") != -1:
            Quetel_Reset = True
            Quetel_Reset_LastTime = time.strftime('%d%b%Y_%H%M%S')
            self.ResetInLastCycle = True
        else:
            self.ResetInLastCycle = False
            
        if self.ResetInLastCycle:
            print "QUECTEL RESET in last cycle!"
     
        return self.ResetInLastCycle
             
         
           
        
    

class clsSql():

    def Select_Configurations(self):
        global IdTransportista
        global IdUnidad
        global SYSTEM_CONFIGURATIONS_SQL

        SYSTEM_CONFIGURATIONS_SQL = False
        try:
            conn = sqlite3.connect('/home/pi/innobusmx/data/db/aforo')
            c = conn.cursor()
            if IdTransportista  == "" or IdUnidad  == "":
                c.execute("SELECT idTransportista, idUnidad FROM configuraSistema")
                data = c.fetchone()
                print data
                IdTransportista = str(data[0])
                IdUnidad = str(data[1])
                if IdTransportista  != "" or IdUnidad  != "":
                    SYSTEM_CONFIGURATIONS_SQL = True
        except:
            print "ERROR: Select_Configurations"
        if SYSTEM_CONFIGURATIONS_SQL:
            print "SYSTEM CONFIGURATIONS SQL Succesfully!"
            return True
        else:
            print "SYSTEM CONFIGURATIONS SQL Fail!"
            return False
          
    
   ###################################################
   #           FINAL DE CODIGO AGREGADO POR          #
   #                  RENE  DELGADO                  #
   ###################################################




class mainWin():

    def __init__(self):
        global SYSTEM_CONFIGURATIONS_SQL
        self.oSql = clsSql()
        self.oQuectel = clsQuectel() 
        #self.oQuectel.Restart()
        
        if not SYSTEM_CONFIGURATIONS_SQL:
            self.oSql.Select_Configurations()       
        
        while(1):
            if self.oQuectel.TresG_Connection(2):
                if self.oQuectel.PDP_Configuration(2):
                    if self.oQuectel.GPS_Connection(2):
                        self.oQuectel.TCP_Configuration(3)
                    self.oQuectel.HTTP_Post()

                    #Comentado por Abel M. 2017-10-13 11:50
                    #time.sleep(10)
            self.oQuectel.Detect_Reset_With_ATE0()
                   



def main():
    app = QtGui.QApplication(sys.argv)
    ex = mainWin()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

 





