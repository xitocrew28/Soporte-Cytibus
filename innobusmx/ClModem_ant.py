#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4 import QtCore
import StringIO
import serial
from curses import ascii
import time
import os 
import re
import base64
import ftplib
import zipfile
import datetime
import sys
import subprocess

class clQuectel(QtCore.QThread):
# Constantes
    maxSendError = 5
    iMaxSocket = 5
    
    idCons = 0
    lock = False
    sendError = 0
    qData = ()
    flFecha = False
    iSendData = 0
    aforo = False
    flsocket = ""
    flsocketAnt = ""
    stIP = ""
    iNoGPS = 0
    iMaxTryGPS = 120
    
    def __init__(self, parent, clDB, clserial):
        QtCore.QThread.__init__(self)
        self.parent = parent
        self.serial = clserial
        self.clDB = clDB

        c = self.clDB.dbAforo.cursor()
        c.execute(" SELECT idValidador, idTipoTisc, idUnidad, idOperador, csn, saldo, tarifa, fechaHora, folios, enviado FROM validador WHERE enviado = 0 ORDER BY idValidador LIMIT 1")
        data = c.fetchone()
        self.aforo = not (data is None)
        c.close()
        c = None


    def reInitApp(self):
        self.serial.closeSerial()
        self.serial.close3G()
        python = sys.executable
        os.execl(python, python, * sys.argv)

    def writeSer(self, cmd):
        try:
            self.ser.write(cmd)
        except:
            i = 0

    def readlineSer(self):
        try:
            st = self.ser.readline()
        except:
            st = ""
        return st


    def readSer(self, size):
        try:
            st = self.ser.read(size)
        except:
            st = ""
        return st


    def write(self, cmd, answer):
      try:
        intentos = 0
        stReadAnt = ""
        #print "Tx >>>> ",cmd
        answer += ("closed", "pdpdeact",)
        stRead = ""
        self.ser.write(cmd.encode())
        find = False
        while not find and intentos < 20:
            stRead += self.readlineSer()           
            for  j in answer:
                if ( stRead.find(j) != -1):
                    #print "Find: " + j
                    find = True
                    break
            #print "Ant: ("+str(len(stReadAnt))+")  "+stReadAnt+" - stRead: ("+str(len(stRead))+") "+stRead
            if (len(stRead) == len(stReadAnt)):
                intentos += 1
            else:
                intentos = 0        
            stReadAnt = stRead
        if (intentos == 20):
            #self.parent.flSocket = False
            print "Tx Err (20) >>>> ",cmd
            stRead = ""
            self.ser.write("\x1A\r")
        if (stRead.find("pdpdeact") != -1):
            self.ser.write("\x1A\r")
            self.parent.flSocket = False
            print "Tx >>>> ",cmd
            print "WRITE ----- stRead",stRead
            self.reInicializaConexion()
        if (stRead.find("closed") != -1):
            self.ser.write("\x1A\r")
            self.parent.flSocket = False
            print "Tx >>>> ",cmd
            print "WRITE ----- stRead",stRead
            self.reInicializaTCP()
            #self.reInicializaConexion()
      except:
            print "Cerrando Modem 3G"
            self.serial.close3G()
            self.ser = None
            while (self.ser == None):
                self.ser = self.serial.init3G()

            self.setupModem()
            stRead = ""
            #self.parent.flGPSOK = False
            #self.parent.flGPS = False
      #print "return "+stRead+"   ("+str(intentos)+")"
      return stRead

    def setupModem(self):
        self.idCons = 0
        self.flG = False
        self.flR = True
        paso = 0
        print '### Iniciando el modulo de comunicaciones ###'
        print '###                v0.10                  ###'
        print '#############################################'       

        self.flFTP = False
        self.flRed = False
        self.flSocket = False
        self.iComm = 0
        self.flSIM = False
        self.stFecha = "" 

        ini = ''

        self.initModem()
        self.inicializaPDP()
        #self.inicializaTCP()
        self.syncFecha()
        self.syncVersion()

    def initModem(self):
        self.reset()
        self.validaSIM()

        self.configuraGPS()
        self.configuraAPN()
        self.configuraFTP()
        self.configuraSMS()
        
    def reset(self):
	print '### Reiniciando Modem                     ###'
        st = ""
        self.writeSer("\x1A\r")
        self.writeSer("AT+QPOWD\r")
        stAnt = ""
        i = 0
        while ((st.find("RDY") == -1)):
            st += self.readlineSer()
            #print len(st),"st",st
            if len(st) == len(stAnt):
                #print "= st",st
                time.sleep(5)
                i += 1
            else:
                i = 0
            if (st.find("ERROR") != -1) or (i == 5):
                self.serial.close3G()
                self.ser = self.serial.init3G()
                self.writeSer("AT+QPOWD\r")
                #os.system("sudo reboot")
                #print "sudo reboot"
                i = 0
                st = ""
            stAnt = st
        stRead = self.write('AT+CTZU?\r', ("OK", "OK"))
        #print stRead
        if stRead.find("CTZU: 0") != -1:
            stRead = self.write('AT+CTZU=1\r', ("OK", "ERROR"))
            os.system("sudo reboot")
        self.writeSer('ATE0\r')
	print '###                           Reinicio OK ###'


    def run(self):
        self.ser = self.serial.init3G()
        if (self.ser != None):
            self.setupModem()
        while True:
            if (self.ser != None):
                self.obtenerCoordenadaGPS()
                self.obtenerMensaje()
            else:
                self.ser = self.serial.init3G()    
                if (self.ser != None):
                    self.setupModem()
            time.sleep(1)

    def configuraGPS(self):
        print '### Iniciando GPS                         ###'
        self.parent.flGPSOK = False
        stRead = self.write("AT+QGPSEND\r",("OK\r", "ERROR"))
        time.sleep(1)
        stRead = self.write("AT+QGPSDEL=0\r",("OK\r", "ERROR"))
        time.sleep(1)
        stRead = self.write("AT+QGPS=1\r",("OK\r", "+CME ERROR"))
        if (stRead.find("OK") != -1):
            print '###                                GPS OK ###'
            self.parent.flGPSOK = True
	else:
            if (stRead.find("504") != -1):
                print '###                             El GPS ON ###'
                self.parent.flGPSOK = True
            else:
                print '                          ERROR EN EL GPS ###'

    def validaSIM(self):
        i = 0
        self.parent.iccid = ""
        print '### VALIDAR MODULO SIM                    ###'
        self.parent.flSIM = False
        while (not self.parent.flSIM):
            stRead = self.write("AT+CPIN?\r",("OK","+CME ERROR"))
            #print "CPIN? "+stRead
            if(stRead.find("OK") != -1):
                print '###                         MODULO SIM OK ###'
                print '### VALIDAR REGISTRO SIM                  ###'
                stRead = self.write("AT+CCID\r",("OK","ERROR"))
                #print "CCID "+stRead
                if(stRead.find("+QCCID:") != -1):
                    stRead = " ".join(stRead.split())
                    j = stRead.find("+QCCID:")
                    self.parent.iccid = stRead[j+8:j+28]
                    while (not self.parent.flSIM):        
                        stRead = self.write("AT+CREG?\r",("OK","+CME ERROR"))
                        #print "CREG? "+stRead
                        if(stRead.find("+CREG: 0,1") != -1):
                            print '###                    REGISTRO EN RED OK ###'
                            self.parent.flSIM = True
                        else:
                            print '###              FALLO DE REGISTRO EN RED ###',i
                            time.sleep(20)
                            i += 1
                else:
                    print '###                      ERROR LEER ICCID ###'
            else:
                print '###                  ERROR EN TARJETA SIM ###'
                time.sleep(20)
                i += 1
            if (i == 10):
                self.initModem()
                i = 0
                

    def configuraAPN(self):
        print '### CONFIGURAR APN                        ###'
        cmd =   'AT+QICSGP=1,1,"%s","%s","%s",1\r' % (self.clDB.urlAPN, self.clDB.userAPN, self.clDB.pwdAPN)
        flAPNOK = False
        while (not flAPNOK):
            stRead = self.write(cmd, ("OK", "ERROR"))
            # print "CMGF: "+stRead
            # stRead = " ".join(stRead.split())
            if (stRead.find("OK") == -1):
                print '###               FALLO AL CONFIGURAR ANP ###'
                stRead = self.write('AT+QIDEACT=1\r', ("OK", "ERROR"))
            else:
                print '###                  CONFIGURACION APN OK ###'	    
                flAPNOK = True

    def configuraFTP(self):	
	print '### CONFIGURACION FTP                     ###'
        stRead = self.write("AT+QICSGP=1\r", ("OK", "ERROR"))
        cmd ='AT+QFTPCFG="account","%s","%s"\r'% (self.clDB.userFTP, self.clDB.pwdFTP)
        stRead = self.write(cmd, ("OK", "ERROR"))
        stRead = self.write('AT+QFTPCFG="filetype",0\r', ("OK", "ERROR"))
        stRead = self.write('AT+QFTPCFG="transmode",0\r', ("OK", "ERROR"))
        stRead = self.write('AT+QFTPCFG="contextid",1\r', ("OK", "ERROR"))
        stRead = self.write('AT+QFTPCFG="rsptimeout",20\r', ("OK", "ERROR"))
        stRead = self.write('AT+QFTPCFG="ssltype",0\r', ("OK", "ERROR"))
        stRead = self.write('AT+QFTPCFG="sslctxid",1\r', ("OK", "ERROR"))
        print '###                       CONEXION FTP OK ###'

    def configuraSMS(self):
        print '### Configuracion SMS                     ###'
        flSMS = False
        while (not flSMS):
            stRead = self.write("AT+CMGF=1\r",("OK", "ERROR"))
            #print "CMGF: "+stRead
            if(stRead.find("OK") != -1):
                print '###                         MODULO SMS OK ###'
                flSMS = True
            else:
                print '###                   ERROR en Modulo SMS ###'
                time.sleep(1)

    def inicializaPDP(self):
        print '### INICIALIZANDO CONEXION PDP            ###'
        self.parent.flRed = False
        iPDP = 0
        iMaxPDP = 20
        while (not self.parent.flRed):
            stRead = self.write("AT+QIACT?\r", ("OK","ERROR"))
            #print "AT+QIACT?: "+stRead
            if (stRead.find("+QIACT: 1,1,1") != -1):
                stRead = self.write('AT+QIDEACT=1\r', ("OK", "ERROR"))
                stRead = self.write('AT+QIACT=1\r', ("OK", "ERROR"))
                print '                        Conx PDP Conf Ant ###'
                self.flsocket = stRead
                if (self.flsocket != self.flsocketAnt):
                    self.flsocketAnt = self.flsocket
                self.parent.flRed = True
            else:
                self.parent.flRed = False
                if (stRead.find("ERROR") != -1):
                    print '###            ERROR EN ACTIVACION DE PDP ###',datetime.datetime.now().time()
                    time.sleep(10)
                    iPDP += 1
                else:
                    stRead = self.write('AT+QIDEACT=1\r', ("OK", "ERROR"))
                    stRead = self.write('AT+QIACT=1\r', ("OK", "ERROR"))
                    if (stRead.find("OK") != -1):
                        stRead = self.write("AT+QIACT?\r", ("OK","ERROR"))
                        #print "AT+QIACT?: "+stRead
                        if (stRead != ""):
                            self.stIP = " ".join(stRead.split())
                            self.stIP = self.stIP.split(" ")
                            self.stIP = self.stIP[1].split(",")
                            if (len(self.stIP) > 2):
                                self.stIP = self.stIP[3][1:-1]
                                self.parent.flRed = True
                            else:
                        	self.write('ATE0\r',("OK","OK"))
                                self.stIP = ""
                                iPDP += 1
                                print '###                   FALLO AL Obtener IP ###'
                                time.sleep(10)
                            self.flsocket = stRead
                        print '###                     ACTIVACION PDP OK ###',datetime.datetime.now().time(), "  ", self.stIP
                    else:
                        print '###               FALLO AL Re-ACTIVAR PDP ###'
                        time.sleep(10)
                        iPDP += 1
            if (iPDP == iMaxPDP):
                self.initModem()
                iPDP = 0 
        self.inicializaTCP()

    def inicializaTCP(self):
        cmd =  'AT+QIOPEN=1,0,"TCP","%s",%s,0,0\r' % (self.clDB.urlSocket, self.clDB.puertoSocket)
        self.parent.flSocket = False
        while (not self.parent.flSocket):
            stRead = self.write(cmd, ("QIOPEN", "ERROR"))
            #print "QIOPEN: "+stRead
            print '### CONEXION TCP                          ###',datetime.datetime.now().time()
            if(stRead.find("QIOPEN: 0,0") != -1):
                print '###                       CONEXION TCP OK ###',datetime.datetime.now().time()
                self.parent.flSocket = True
            else:
                if(stRead.find('562') != -1):
                    print '###                           TCP ABIERTA ###',datetime.datetime.now().time()
                    self.parent.flSocket = True
                else:
                    print '###                             ERROR TCP ###',datetime.datetime.now().time()
                    time.sleep(30)

    def senial3G(self):
        senial = 0
        stRead = self.write('AT+CSQ\r', ("OK", "ERROR"))
        #print "CSQ: "+stRead
        #print "pos: ", stRead, "pos[10]: ", stRead[10]
        if (stRead.find("OK") != -1):
            i = stRead.find("+CSQ:")
            if (i != -1):
                i = 9
                if (stRead[10] == ","):
                    i = 10
                #print "signal",stRead[7:i]
                try:
                    senial = int(stRead[7:i])
                except:
                    print "Error: Casting int() SignalQuality.", stRead[7:i],"  ",stRead
                    self.write('ATE0\r',("OK","OK"))
                #print "Senial (",stRead[:i+8],")",senial
                self.parent.iComm = senial
            else:
                print "Error: Return SignalQuality.",stRead
                self.parent.iComm = 0
        else:
            print "Error: SignalQuality.",stRead
            self.parent.iComm = 0

        return senial


    def reInicializaConexion(self):
        print '###  Reiniciando Conexion General        ###'
        #self.ser.write("+++\r\x1A\r")
        self.writeSer("\x1A\r")
        stRead = self.write('AT+QICLOSE=0\r', ("OK", "ERROR"))
        stRead = self.write('AT+QIDEACT=1\r', ("OK", "ERROR"))
        self.write('ATE0\r',("OK","OK"))
        self.inicializaPDP()
        #self.inicializaTCP()
        
        
    def reInicializaPDP(self):
        print '###           Cerrando conexion  PDP      ###'
        self.writeSer("\x1A\r")
        stRead = self.write('AT+QIDEACT=1\r', ("OK", "ERROR"))
        self.write('ATE0\r',("OK","OK"))
        self.inicializaPDP()
        #self.reInicializaTCP()


    def reInicializaTCP(self):
        print '###           Cerrando conexion  TCP      ###'
        self.writeSer("\x1A\r")
        stRead = self.write('AT+QICLOSE=0\r', ("OK", "ERROR"))
        self.write('ATE0\r',("OK","OK"))
        #print "QICLOSE=0"+stRead
        #if (stRead.find("OK") != -1):
        #    print '###       Reiniciando Conexion TCP       ###'
        self.inicializaTCP()


    def sendData(self, data):
        self.lock = True
        result = ""
        senial = self.senial3G()
        #print "Senial: ",str(senial)
        if senial > 5 and senial  != 99 and self.parent.flRed and self.parent.flSocket:
            stRead = self.write('AT+QISEND=0\r', ("ERROR", "OK", '>')) 
            if (stRead.find(">") != -1):
                cmd = data+"\r\x1A\r"
                stRead = self.write(cmd,('recv', 'ERROR'))
                if (stRead.find('"recv",0') != -1):
                    result = self.write('AT+QIRD=0\r', ("OK", "ERROR"))
                    self.iSendData = 0
                elif (stRead.find('ERROR') != -1) or (self.sendError == self.maxSendError):
                    cmd = "\x1A\r"
                    stRead = self.write(cmd,('OK', 'ERROR'))
                    self.reInicializaConexion()
                else:
                    self.sendError += 1
                    cmd = "\x1A\r"
                    stRead = self.write(cmd,('OK', 'ERROR'))
            elif (stRead.find("ERROR") != -1):
                self.reInicializaPDP()
            else:
                self.writeSer("\x1A\r")
                #cmd = "\x1A\r"
                #stRead = self.write(cmd,('OK', 'ERROR'))
                self.iSendData += 1
                #print "stRead",stRead, "Error: Send Data no > ",self.iSendData
        else:
            self.iSendData += 1
            time.sleep(60)
            if not self.parent.flRed:
                print "Error: No hay conexion de Red. PDP"                    
            elif not self.parent.flSocket:
                print "Error: No hay conexion con el Servidor TCP"                    
            else:
                print "Error: Bad SignalQuality."                    

        #if (self.iSendData == 5):
        #    self.reInicializaConexion()
        #    self.iSendData = 0
        self.lock = False
        return result

  
    def syncFecha(self):

        comando = ""
        while (not self.parent.flFecha):
            print '###   Sincronizando Fecha con Proveedor   ###'
            stRead = self.write("AT+CCLK?\r",("OK","OK"))
            #print "CCLK? "+stRead
            i = stRead.find('"')
            #print "Fecha: ",int(stRead[i+19:i+21])
            if (stRead != ""):
                try:
                    if (int(stRead[i+1:i+3]) > 17 and int(stRead[i+1:i+3]) < 50):
                        stFecha = "20"+stRead[i+1:i+3]+"-"+stRead[i+4:i+6]+"-"+stRead[i+7:i+9]+" "+stRead[i+10:i+18]
                        fecha = datetime.datetime(int("20"+stRead[i+1:i+3]), int(stRead[i+4:i+6]), int(stRead[i+7:i+9]), int(stRead[i+10:i+12]), int(stRead[i+13:i+15]), int(stRead[i+16:i+18])) - datetime.timedelta(hours=int(stRead[i+19:i+21])/4)
                        stFecha = fecha.strftime("%Y/%m/%d %H:%M:%S")
                        #print "Fecha local: ",stFecha
                        comando = 'sudo date --set "%s"'%str(stFecha)
                        #print "comando",comando
                        self.parent.flFecha = True
                        print '###  FECHA Proveedor',stFecha
                        self.stFecha = "RED"
                    else:        
                        print '###                  No hay Servicio      ###'
                        print '###   Sincronizando fecha con Servidor    ###'
                        i = 0
                        fecha = self.sendData("0,"+str(self.clDB.idUnidad))
                        if (fecha != ""):
                            fecha = " ".join(fecha.split()) #se le aplica un split al mismo comando
                            fecha = fecha.split(' ')
                            #print "fecha: ",fecha
                            stRead = "\""+fecha[2]+' '+fecha[3]+"\""
                            print '###   Fecha Servidor '+stRead+'         ###'
                            comando = 'sudo date --set %s'%str(stRead)
                            self.parent.flFecha = True
                            self.stFecha = "SERVIDOR"
                            #self.parent.flRed = True
                            #self.parent.flFecha = True
                        else:
                            print '###                  No hay Conexionv   ###'
                except:
                    print "Error:",stRead
                        
                        
        if (comando != ""):
            os.system(comando)
            self.clDB.insertBitacora(stRead)


    def obtenerCoordenadaGPS(self):
        stRead = self.write('AT+QGPSLOC=2\r', ("OK", "ERROR"))
        self.parent.flGPS = (stRead.find("OK") != -1)
        stGPS = ""
        if(self.parent.flGPS):
	    stRead = " ".join(stRead.split())
	    my_list = stRead.split(",")
            # 0 Hora  (hh-mm-ss)
	    # 1 latitud
	    # 2 longitud
            # 7 velocidad
            # 9 Fecha (dd-mm-aa)
            if (len(my_list) == 11):
                self.iNoGPS = 0
                #hora = my_list[0][10:12] + ":" + my_list[0][12:14] + ":" + my_list[0][14:16]
                latitud = my_list[1]
                longitud = my_list[2]
                velGPS = my_list[7]
                datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
                #fecha = "20"+my_list[9][4:6] + "-" + my_list[9][2:4] + "-" + my_list[9][0:2]
                idInser = my_list[9][0:2]+my_list[0][10:16]
                self.idCons += 1
                self.parent.lblVelocidad.setText(str(velGPS))
                #datetimes = fecha + ' ' + hora
                stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(datetimes)+','+str(latitud)+','+str(longitud)+','+str(velGPS)+','+str(self.idCons)+'\r'+''
                stGPS = self.sendData(stGPS)
                if stGPS == "......":
                    fl = True
                    while fl:
                        try:
                            self.clDB.dbGPS.execute('INSERT INTO tgps (hora, latitud, longitud, fecha, velocidad, idPos, enviado, idCons) VALUES (?, ?, ?, ?, ?, ?, 0, ?)', (hora, latitud, longitud, fecha, velGPS, idInser, self.idCons))
                            self.clDB.dbGPS.commit()
                            fl = False
                        except:
                            fl = False
                            print "error en el insert del GPS"
            else:
                print my_list
                print "###              Error> Lista mal formada ### "
                    
        else:
            self.iNoGPS += 1
            #print "iNoGPS (",self.iNoGPS,")",stRead
            #time.sleep(self.iNoGPS*60)
            velGPS = 0
            self.parent.lblVelocidad.setText("-")
            if (self.iNoGPS == self.iMaxTryGPS):
                self.configuraGPS()
                self.iNoGPS = 0
        if (stGPS == ""):
            stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,0,0,0,0\r'
            stGPS = self.sendData(stGPS)
        stGPS = ''.join(stGPS)
        stGPS = stGPS.split("\r\n")
        #print "stGPS: (", len(stGPS) , ")", stGPS
        
        if (len(stGPS) > 1):
            stGPS = stGPS[2].split("@")
            if (len(stGPS) > 1):
                if (stGPS[1] == "R"):
                    stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,1,0,0,0\r'
                    stGPS = self.sendData(stGPS)
                    os.system("sudo reboot")
                if (stGPS[1] == "r"):
                    stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,1,0,0,0\r'
                    stGPS = self.sendData(stGPS)
                    self.reInitApp()
                if (stGPS[1] == "u"):
                    if self.syncVersion():
                        stGPS = self.sendData(stGPS)
                if (stGPS[1] == "9"):
                    self.descargarFotografia(stGPS[2])
#                if (stGPS[1] == "b"):
#                    os.system("sudo chmod 777 "+stGPS[2])
#                    os.system(stGPS[2])
#                if stAforo[2] == "1":
#                    self.clDB.dbAforo.execute('DELETE FROM validador WHERE idValidador = '+str(data[0]))
#                    self.clDB.dbAforo.commit()
        if (self.aforo):
            c = self.clDB.dbAforo.cursor()
            c.execute(" SELECT idValidador, idTipoTisc, idUnidad, idOperador, csn, saldo, tarifa, fechaHora, folios, enviado FROM validador WHERE enviado = 0 ORDER BY idValidador LIMIT 1")
            data = c.fetchone()
            if not (data is None):
                print '###       Si hay Aforos nuevos      ###'
                stAforo = '3,'+str(data[1])+','+str(data[2])+','+str(data[3])+','+str(data[4])+','+str(data[5])+','+str(data[6])+','+str(data[8])+','+str(data[7])+'\r'+''
                print '###      Dato a enviar en validacion      ###'
                #print(stAforo)
                salgo = 0
                #self.procesoDeEnvio(validadorS, idValida, accion, salgo)
                stAforo = self.sendData(stAforo)
                if (stAforo != ""):
                    stAforo = ''.join(stAforo)
                    stAforo = stAforo.split("\r\n")
                    #print "datos: (", len(stAforo) , ")", stAforo
                    if (len(stAforo) > 3):
                        #print len(stAforo), "  stAforo: ",stAforo
                        if stAforo[2] == "1":
                            self.clDB.dbAforo.execute('DELETE FROM validador WHERE idValidador = '+str(data[0]))
                            self.clDB.dbAforo.commit()
            else:
                self.aforo = False
            c.close()
            c = None 


    def multiwordReplace(text, wordDic):
        """
        take a text and replace words that match a key in a dictionary with
        the associated value, return the changed text
        """
        rc = re.compile('|'.join(map(re.escape, wordDic)))
        def translate(match):
            return wordDic[match.group(0)]
        return rc.sub(translate, text)

    def syncVersion(self):
        print '### Sincronizando Versiones del Validador ###'
        dato = self.sendData("I,"+str(self.clDB.idUnidad)+","+self.parent.iccid+","+self.parent.serialNumber+","+self.parent.stVersion+","+self.parent.version+","+self.stFecha+","+self.stIP+","+str(self.clDB.economico))
        print '###  Sincronizando Software con Servidor  ###'
        i = 0
        dato = self.sendData("S,0,"+str(self.clDB.idUnidad)+",Prepago")
        dato = " ".join(dato.split()) #se le aplica un split al mismo comando
        dato = dato.split('@')
        if (len(dato) > 2):
            self.parent.flFTP = True
            self.parent.lblNombreOperador.setText("Actualizando Software "+self.parent.stVersion)
            cmd =  'AT+QFTPOPEN="%s",%s\r' % (self.clDB.urlFTP, self.clDB.puertoFTP)
            stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"))
            print '### CONEXION FTP                          ###'
            if(stRead.find("QFTPOPEN: 0,0") != -1) or (stRead.find('530') != -1):
                if(stRead.find('530') != -1):
                    print '###                           FTP ABIERTA ###'
                else:
                    print '###                       CONEXION FTP OK ###'
                if (self.descargarArchivoFTP(dato[2],dato[3], True)):
                    stRead = self.sendData("S,1,"+str(self.clDB.idUnidad)+","+dato[2])

                    if (dato[4] == "r"):
                        stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,1,0,0,0\r'
                        stGPS = self.sendData(stGPS)
                        self.reInitApp()
                    if (dato[4] == "R"):
                        stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,1,0,0,0\r'
                        stGPS = self.sendData(stGPS)
                        #print "Reboot:",dato[4]
                        os.system('sudo reboot')
                    if (dato[4] == "A"):
                        stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,1,0,0,0\r'
                        stGPS = self.sendData(stGPS)
                        self.serial.closeSerial()
                        os.system('avrdude -v -patmega328p -Uflash:w:/home/pi/'+dato[3]+':i -carduino -b 115200 -P '+self.serial.sPort)
                        os.remove(dato[3])
                        self.reInitApp()
                else:
                    print '###              ERROR LEER ARCHIVOFTP ###'
            else:
                print '###                             ERROR FTP ###'
            self.parent.lblNombreOperador.setText("")
            stRead = self.write("AT+QFTPCLOSE\r", ("QFTPCLOSE:", "ERROR"))
            self.parent.flFTP = False

    def descargarArchivoFTP(self, origen, destino, msg):
        print '###                       Inicia Descarga ###'
        cmd = 'AT+QFTPSIZE="%s"\r'%(origen)
        stRead = self.write(cmd, ("QFTPSIZE", "ERROR"))
        iLenFile = 0
        stFind = ""
        if (stRead.find("QFTPSIZE") != -1):
            stRead = stRead.split("\r\n")
            stRead = stRead[3].split(" ")
            stRead = stRead[1].split(",")
            if (stRead[0] == "0"):
                iLenFile = int(stRead[1])
                stFind = "+QFTPGET: 0,"+stRead[1]
        if (stFind != ""):
            cmd = 'AT+QFTPGET="%s","COM:"\r'%(origen)
            print str(iLenFile)+"   "+origen
            stRead = ""
            self.writeSer(cmd.encode())
            find = -1
            error = False
            fl = False
            size = 0
            iError = 0
            with open(destino+".tmp", 'wb') as f:
                stAnt = ""
                st = ""
                while (find == -1) and not error:
                    stRead = self.readSer(1024)
                    #print stRead
                    if (stRead != ""):
                        if (not fl):
                            i = stRead.find("CONNECT")
                            if (i != -1):
                                stRead = stRead[i+9:]
                                fl = True
                        st = stAnt + stRead
                        find = st.find(stFind)
                        error = (st.find("CME ERROR" ) != -1)
                        if not error and (find == -1) and (stAnt != ""):
                            f.write(stAnt)
                        elif not error and (find != -1):
                            f.write(st[:find-8])
                        stAnt = stRead
                        iError = 0
                        size += len(stRead)
                        if msg:
                            self.parent.lblNombreOperador.setText("Actualizando Software "+str(size))
                        #print "Leido: ",size
                    else:
                        iError += 1
                        error = (iError == 10)
            if error:
                print "Error (",str(iError),")", st
                os.remove(destino+".tmp")
                return False
            else:
                if (destino.find(".zip") != -1):
                    print '###                      Unzipping File   ###'
                    os.rename(destino+".tmp", destino)
                    zip_ref=zipfile.ZipFile(destino,'r')
                    zip_ref.extractall('/home/pi/innobusmx')
                    zip_ref.close()
                    os.remove(destino)
                else:
                    if os.path.exists(destino):
                        os.remove(destino)
                    os.rename(destino+".tmp", destino)
                return True
        else:
            print "Error (",stRead,")"
            return False
        
            
    def descargarFotografia(self, csn):
        print '###                Descarga Fotografia ###'
        cmd =  'AT+QFTPOPEN="%s",%s\r' % (self.clDB.urlFTP, self.clDB.puertoFTP)
        stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"))
        print '### CONEXION FTP                          ###'
        fl = False
        self.parent.flFTP = True
        if(stRead.find("QFTPOPEN: 0,0") != -1) or (stRead.find('530') != -1):
            if(stRead.find('530') != -1):
                print '###                           FTP ABIERTA ###'
            else:
                print '###                       CONEXION FTP OK ###'

            path = '/home/pi/innobusmx/data/user/'+csn[0:5]
            origen = "Prepago\\Prepago\\FTP Share\\Fotos\\"+csn+".jpeg"
            if os.path.exists(path+"/"+csn+".Jpeg"):
                sizeLocal = os.path.getsize(path+"/"+csn+".Jpeg")
            else:
                sizeLocal = 0
            cmd = 'AT+QFTPSIZE="%s"\r'%(origen)
            stRead = self.write(cmd, ("QFTPSIZE", "ERROR"))
            iLenFile = 0
            stFind = ""
            if (stRead.find("QFTPSIZE") != -1):
		stRead = " ".join(stRead.split()) #se le aplica un split al mismo comando
		stRead = stRead.split(",")
                iLenFile = int(stRead[1])
                stFind = "+QFTPGET: 0,"+stRead[1]
            cmd = 'AT+QFTPGET="%s","COM:"\r'%(origen)
            print str(sizeLocal)+"  "+str(iLenFile)+"   "+csn+".jpeg"
            if (sizeLocal != iLenFile):
                if not os.path.exists(path):
                    os.mkdir(path)
                stRead = ""
                self.writeSer(cmd.encode())
                find = -1
                error = False
                size = 0
                iError = 0
                with open(path+"/"+csn+".Jpeg.tmp", 'wb') as f:
                    stAnt = ""
                    st = ""
                    while (find == -1) and not error:
                        stRead = self.readSer(1024)
                        if (stRead != ""):
                            if (not fl):
                                i = stRead.find("CONNECT")
                                if (i != -1):
                                    stRead = stRead[i+9:]
                                    fl = True
                            st = stAnt + stRead
                            find = st.find(stFind)
                            error = (st.find("CME ERROR" ) != -1)
                            if not error and (find == -1) and (stAnt != ""):
                                f.write(stAnt)
                            elif not error and (find != -1):
                                f.write(st[:find-8])
                            stAnt = stRead
                            iError = 0
                            size += len(stRead)
                            #print "Leido: ",size
                        else:
                            iError += 1
                            error = (iError == 10)
                if error:
                    print "Error: ("+str(iError)+")"
                    os.remove(path+"/"+csn+".Jpeg.tmp")
                    fl = False
                else:
                    print "Foto OK: "+csn+".Jpeg."
                    os.rename(path+"/"+csn+".Jpeg.tmp", path+"/"+csn+".Jpeg")
                    fl = True
            else:
                print "Foto Repetida: "+csn+".Jpeg."
                fl = True
                
        stRead = self.write("AT+QFTPCLOSE\r", ("+QFTPCLOSE", "ERROR"))
        if fl:
            stRead = self.sendData("9,"+csn+","+str(self.clDB.idUnidad))                
        self.parent.flFTP = False            
        return fl        


    #Agregados para mensaje
    def obtenerMensaje(self):
        '''
        ##################################################
        #                 Lectura de SMS                 #
        ##################################################
        '''
        #print '### Lectura de mensajes ###'
        nSMS = 1
        comando = self.write("AT+CMGR=%s\r"%nSMS,("OK", "ERROR"))
        comandoS = comando.rstrip()
        comandoT = ",".join(comandoS.split())
        #print 'evaluo',  comandoT[0:6]
        if str(comandoT[0:6]) == '+CMGR:':
            text = comandoT.split(',')
            print 'Text', text
            try:
                cmd = text[8]
                #este pasa cuando hay una actualizacion por lo que
                #obtendre el comando sin la actualizacion
                if cmd[:2] == 'IU':
                    #print 'Actualizacion de algo'
                    strActualizacion = cmd
                    cmd = cmd[:6]
                    print strActualizacion
                else:
                    #esto pasa cuando es un comando normal
                    cmd = text[8]
                    print cmd
                    strActualizacion = 'nulo'
            except:
                print 'Mensaje sms no valido'
                cmd = 'ERROR'
                strActualizacion = 'nulo'
            self.validarComando(cmd, strActualizacion, nSMS)
            #print 'validar comando'
        nSMS = nSMS + 1
        #self.entrarAccionSiete = 0        

    def validarComando(self, comando, strActualizacion, sms):
        #comando = 'IREUC'
        
        if(comando.find("OK") != -1):
                comando = self.write("AT+CMGR=1\r",("OK", "ERROR"))                          
                print '###  ###'
                i = comando.find("+CMGR:")
                j = comando.find("OK")                              
                comando=comando[i+56:j-4] 
        
        c= self.clDB.dbComando.cursor()
        print "select validarComando"
        c.execute("SELECT comando, accion, dEjec FROM tComando WHERE comando = ?",(comando, ))
        print "fetch validarComando"  
        data = c.fetchone()
        print data
        if data is None:
            print 'Comando no valido'
        else:
            comaT = data[0]
            acciT = data[1]
            dEjeT = data[2]
        #print execc
        print "close cursos validarComando"  
        c.close()
        c = None

        if data is None:
            print '###           Comando no soportado        ###'
            cmd = 'AT+CMGD=%s\r'%str(sms)
            self.writeSer(cmd.encode())
            mensaje = self.readSer(128)
        else:
            if dEjeT == 'L':
                #local execute
                exec acciT
                #Elimino el comando SMS
                cmd = 'AT+CMGD=%s\r'%str(sms)
                self.writeSer(cmd.encode())
                mensaje = self.readSer(128)
            if dEjeT == 'C':
                #console execute
                cmd = 'AT+CMGD=%s\r'%str(sms)
                self.writeSer(cmd.encode())
                mensaje = self.readSer(128)
                
                return_code = subprocess.call("%s"%str(acciT), shell=True)
                print return_code
                #Elimino el comando SMS
                
                
            if dEjeT == 'o':
                print acciT
                #Elimino el comando SMS
                cmd = 'AT+CMGD=%s\r'%str(sms)
                self.writeSer(cmd.encode())
                mensaje = self.readSer(128)
                
                
                
            if dEjeT == 'S':
                print 'Comando', comando
                print 'strComando', strActualizacion

                #print "Connect comando accion"  
                #connC = sqlite3.connect(cdDbC)
                print "cursos comando accion"  
                c= dbComando.cursor()
                print "select comando accion"  

                c.execute("SELECT accion FROM tComando WHERE comando = ?",(comando,))
                print "fetch comando accion"  
                datosComando = c.fetchone()
                print "close comando accion"  
                c.close()
                c = None
                if datosComando is None:
                    print('No hay parametros de configuracon contacta al \
                        administrador')
                else:
                    accion = datosComando[0]

                print  strActualizacion.split("@")
                obtDatoActualizar =  strActualizacion.split("@")
                datoAActualizar = obtDatoActualizar[1]

                print accion.split(",")
                datosDeBase = accion.split(",")
                nombreTabla = str(datosDeBase[0])
                nombreRow = str(datosDeBase[1])
                nombreBase = str(datosDeBase[2])

                print 'Nueva pagina', datoAActualizar
                print 'Donde lo voy a guardar', nombreTabla
                print 'Nombre del campo a afectar', nombreRow
                print 'Nombre de la base que voy a alterar', nombreBase

                '''
                    Aca empieza el proceso de actualizacion de registro
                    esto va a funcionar para la actualizacion/sincronizacion
                    de los paramtros de configuracion del sistema
                '''
                
                print "update data nombreBase"  
                self.conn.execute('UPDATE ' +'"'+ nombreTabla +'"'+ ' set ' +'"'+ nombreRow +'"'+ ' = ?', (datoAActualizar, ))
                print "commit data nombreBase"  
                self.conn.commit()
                print "close Connect data nombreBase"  
               
                #Elimino el comando SMS
                cmd = 'AT+CMGD=%s\r'%str(sms)
                self.writeSer(cmd.encode())
                mensaje = self.readSer(128)

            else:
                print '###          Comando no soportado         ###'
                cmd = 'AT+CMGD=%s\r'%str(sms)
                self.writeSer(cmd.encode())
                mensaje = self.readSer(128)

        

