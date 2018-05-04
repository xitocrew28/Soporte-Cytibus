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
    aforo = False
    flsocket = ""
    flsocketAnt = ""
    stIP = ""
    iNoGPS = 0
    iMaxTryGPS = 120
    flGetGPS = False
    debug = 1
    
    def __init__(self, parent, clDB, clserial):
        self.iMax = 0
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

    def printDebug(self,msg):
        if self.debug == 1:
            print msg
        if self.debug == 2:
            stRead = self.sendData('d,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S"))+","+msg+"\n")

    def xrun(self):
        try:
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
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            #self.printDebug(sys.exc_info()[1], fname, exc_tb.tb_lineno)
            #file=open("innobusmx/innobus.log","a")
            #file.write('l,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S"))+","+str(sys.exc_info()[1])+","+str(fname)+","+str(exc_tb.tb_lineno)+"\n")
            #file.close()
            #self.run()  


    def run(self):
        self.ser = self.serial.init3G()
        if (self.ser != None):
            self.setupModem()
        while True:
            try:
                if (self.ser != None):
                    self.obtenerCoordenadaGPS()
                    self.obtenerMensaje()
                else:
                    self.ser = self.serial.init3G()    
                    if (self.ser != None):
                        self.setupModem()
                time.sleep(1)
            except:
                  exc_type, exc_obj, exc_tb = sys.exc_info()
##                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
##                    #self.printDebug(sys.exc_info()[1], fname, exc_tb.tb_lineno)
##                file=open("innobusmx/innobus.log","a")
##                file.write('l,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S"))+","+str(sys.exc_info()[1])+","+str(fname)+","+str(exc_tb.tb_lineno)+"\n")
##                file.close()
            #    self.run()  



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
        self.printDebug("Tx >>>> "+cmd)
        answer += ("closed", "pdpdeact",)
        stRead = ""
        self.ser.write(cmd.encode())
        find = False
        while not find and intentos < 5:
            stRead += self.readlineSer()           
            for  j in answer:
                if ( stRead.find(j) != -1):
                    #self.printDebug("Find: " + str(j))
                    find = True
                    break
            #self.printDebug("Ant: ("+str(len(stReadAnt))+")  "+stReadAnt+" - stRead: ("+str(len(stRead))+") "+stRead)
            if (len(stRead) == len(stReadAnt)):
                intentos += 1
                time.sleep(2)
                ##self.printDebug("Intentos: "+str(intentos))
            else:
                intentos = 0        
            stReadAnt = stRead
        if (intentos == 5):
            self.ser.write("\x1A\r")
            self.printDebug("Tx Err (20) >>>> "+cmd)
            stRead = ""
        if (stRead.find("pdpdeact") != -1):
            self.ser.write("\x1A\r")
            self.parent.flSocket = False
            self.printDebug("Tx >>>> "+cmd)
            self.printDebug("WRITE ----- stRead"+stRead)
            self.reInicializaAPN()
        if (stRead.find("closed") != -1):
            self.ser.write("\x1A\r")
            self.parent.flSocket = False
            self.printDebug("Tx >>>> "+cmd)
            self.printDebug("WRITE ----- stRead"+stRead)
            self.reInicializaTCP()
      except:
            self.printDebug('###  I/O Error en el Modem                ###')
            self.serial.close3G()
            self.ser = None
            while (self.ser == None):
                self.ser = self.serial.init3G()

            #self.setupModem()
            self.validaSIM()
            self.inicializaTCP()
            #self.configuraGPS()
            stRead = ""
            #self.parent.flGPSOK = False
            #self.parent.flGPS = False
      self.printDebug("return "+stRead+"   ("+str(intentos)+")")
      return stRead

    def setupModem(self):
        self.idCons = 0
        self.flG = False
        self.flR = True
        paso = 0
        self.printDebug('### Iniciando el modulo de comunicaciones ###')
        self.printDebug('###                v0.10                  ###')
        self.printDebug('#############################################')

        self.flFTP = False
        self.flRed = False
        self.flSocket = False
        self.iComm = 0
        self.flSIM = False
        self.stFecha = "" 

        ini = ''

        #self.reset()
        self.configuraTZ()
        self.validaSIM()
        self.configuraGPS()
        self.configuraAPN()
        self.configuraFTP()
        self.configuraSMS()
        self.inicializaAPN()
        self.inicializaTCP()
        self.syncFecha()
        self.syncLog()
        self.syncVersion()
        #self.debug = 2

    def reset(self):
	self.printDebug('### Reiniciando Modem                     ###')
        st = ""
        self.writeSer("\x1A\r")
        self.writeSer("AT+QPOWD\r")
        stAnt = ""
        i = 0
        while ((st.find("PACSP1") == -1)):
            st += self.readlineSer()
            #self.printDebug(len(st)+" st "+st)
            if len(st) == len(stAnt):
                #self.printDebug("= st "+st)
                time.sleep(5)
                i += 1
            else:
                i = 0
            if (st.find("ERROR") != -1) or (i == 5):
                self.serial.close3G()
                self.ser = self.serial.init3G()
                self.writeSer("AT+QPOWD\r")
                #os.system("sudo reboot")
                #self.printDebug("sudo reboot")
                i = 0
                st = ""
            stAnt = st
        #stRead = self.write('AT+CTZU?\r', ("OK", "OK"))
        #self.printDebug(stRead)
        #if stRead.find("CTZU: 0") != -1:
        #    stRead = self.write('AT+CTZU=1\r', ("OK", "ERROR"))
        #    os.system("sudo reboot")
        #self.writeSer('ATE0\r')
	self.printDebug('###                           Reinicio OK ###')


    def configuraTZ(self):
        reboot = False
	self.printDebug('### Configurando Auto GPS                 ###')
        st = ""
        stRead = self.write('AT+QGPSCFG="autogps"\r', ("OK", "OK"))
        #self.printDebug(stRead)
        if stRead.find('"autogps",0') != -1:
            stRead = self.write('AT+QGPSCFG="autogps",1\r', ("OK", "ERROR"))
            reboot = True
	self.printDebug('### Configurando Zona Horaria             ###')
        st = ""
        stRead = self.write('AT+CTZU?\r', ("OK", "OK"))
        #self.printDebug(stRead)
        if stRead.find("CTZU: 0") != -1:
            stRead = self.write('AT+CTZU=1\r', ("OK", "ERROR"))
            reboot = True
        if reboot:
            os.system("sudo reboot")
        self.writeSer('ATE0\r')
	self.printDebug('###                       Zona Horario OK ###')

    def validaSIM(self):
        i = 0
        self.parent.iccid = ""
        self.printDebug('### VALIDAR MODULO SIM                    ###')
        self.parent.flSIM = False
        while (not self.parent.flSIM):
            stRead = self.write("AT+CPIN?\r",("OK","+CME ERROR"))
            #self.printDebug("CPIN? "+stRead)
            if(stRead.find("OK") != -1):
                self.printDebug('###                         MODULO SIM OK ###')
                self.printDebug('### VALIDAR REGISTRO SIM                  ###')
                stRead = self.write("AT+CCID\r",("OK","ERROR"))
                #self.printDebug("CCID "+stRead)
                if(stRead.find("+QCCID:") != -1):
                    stRead = " ".join(stRead.split())
                    j = stRead.find("+QCCID:")
                    self.parent.iccid = stRead[j+8:j+28]
                    while (not self.parent.flSIM):        
                        stRead = self.write("AT+CREG?\r",("OK","+CME ERROR"))
                        #self.printDebug("CREG? "+stRead)
                        if(stRead.find("+CREG: 0,1") != -1):
                            self.printDebug('###                    REGISTRO EN RED OK ###')
                            self.parent.flSIM = True
                        else:
                            self.printDebug('###              FALLO DE REGISTRO EN RED ### '+str(i))
                            time.sleep(20)
                            i += 1
                else:
                    self.printDebug('###                      ERROR LEER ICCID ###')
            else:
                self.printDebug('###                  ERROR EN TARJETA SIM ###')
                time.sleep(20)
                i += 1
            if (i == 10):
                self.initModem()
                i = 0
                
    def configuraGPS(self):
        self.printDebug('### Iniciando GPS                         ###')
        self.parent.flGPSOK = False
        #stRead = self.write("AT+QGPSEND\r",("OK\r", "ERROR"))
        #time.sleep(1)
        #stRead = self.write("AT+QGPSDEL=0\r",("OK\r", "ERROR"))
        #time.sleep(1)
        stRead = self.write("AT+QGPS=1\r",("OK\r", "+CME ERROR"))
        if (stRead.find("OK") != -1):
            self.printDebug('###                                GPS OK ###')
            self.parent.flGPSOK = True
            self.flGetGPS = True
	else:
            if (stRead.find("504") != -1):
                self.printDebug('###                             El GPS ON ###')
                self.parent.flGPSOK = True
                self.flGetGPS = True
            else:
                self.printDebug('                          ERROR EN EL GPS ###')

    def configuraAPN(self):
        self.printDebug('### CONFIGURAR APN                        ###')
        cmd =   'AT+QICSGP=1\r'
        stRead = self.write(cmd, ("OK", "ERROR"))
        if (stRead.find(self.clDB.urlAPN) != -1):
            self.printDebug('###                                APN OK ###')
            flAPNOK = True
        else:
            flAPNOK = False
            cmd =   'AT+QICSGP=1,1,"%s","%s","%s",1\r' % (self.clDB.urlAPN, self.clDB.userAPN, self.clDB.pwdAPN)
        while (not flAPNOK):
            stRead = self.write(cmd, ("OK", "ERROR"))
            #self.printDebug(cmd+stRead)
            if (stRead.find("OK") == -1):
                self.printDebug('###               FALLO AL CONFIGURAR APN ###')
                stRead = self.write("AT+QIDEACT=1\r",("OK", "OK"))
            else:
                self.printDebug('###                  CONFIGURACION APN OK ###')
                flAPNOK = True

    def configuraFTP(self):	
	self.printDebug('### CONFIGURACION FTP                     ###')
        stRead = self.write("AT+QICSGP=1\r", ("OK", "ERROR"))
        cmd ='AT+QFTPCFG="account","%s","%s"\r'% (self.clDB.userFTP, self.clDB.pwdFTP)
        stRead = self.write(cmd, ("OK", "ERROR"))
        stRead = self.write('AT+QFTPCFG="filetype",0\r', ("OK", "ERROR"))
        stRead = self.write('AT+QFTPCFG="transmode",0\r', ("OK", "ERROR"))
        stRead = self.write('AT+QFTPCFG="contextid",1\r', ("OK", "ERROR"))
        stRead = self.write('AT+QFTPCFG="rsptimeout",20\r', ("OK", "ERROR"))
        stRead = self.write('AT+QFTPCFG="ssltype",0\r', ("OK", "ERROR"))
        stRead = self.write('AT+QFTPCFG="sslctxid",1\r', ("OK", "ERROR"))
        self.printDebug('###                       CONEXION FTP OK ###')

    def configuraSMS(self):
        self.printDebug('### Configuracion SMS                     ###')
        flSMS = False
        while (not flSMS):
            stRead = self.write("AT+CMGF=1\r",("OK", "ERROR"))
            #self.printDebug("CMGF: "+stRead)
            if(stRead.find("OK") != -1):
                self.printDebug('###                         MODULO SMS OK ###')
                flSMS = True
            else:
                self.printDebug('###                   ERROR en Modulo SMS ###')
                time.sleep(1)

    def inicializaAPN(self):
        self.printDebug('### INICIALIZANDO CONEXION APN            ###')
        self.parent.flRed = False
        iPDP = 0
        self.write('ATE0\r',("OK","OK"))
        while (not self.parent.flRed):
            stRead = self.write("AT+QIACT?\r", ("OK","ERROR"))
            #self.printDebug("AT+QIACT?: "+stRead)
            if (stRead.find("+QIACT: 1,1,1") != -1):
                self.printDebug('                        Conx PDP Conf Ant ###')
                if (stRead != ""):
                    self.stIP = " ".join(stRead.split())
                    self.stIP = self.stIP.split(" ")
                    self.stIP = self.stIP[1].split(",")
                    if (len(self.stIP) > 2):
                        self.stIP = self.stIP[3][1:-1]
                        self.printDebug('###                     ACTIVACION PDP OK ### '+str(datetime.datetime.now().time())+"  "+self.stIP)
                        self.parent.flRed = True
                    else:
                        self.stIP = ""
                        iPDP += 1
                        self.printDebug('###                   FALLO AL Obtener IP ###')
                        time.sleep(10*iPDP)
            elif (stRead.find("ERROR") != -1):
                self.printDebug('###            ERROR EN ACTIVACION DE PDP ###'+str(datetime.datetime.now().time()))
                iPDP += 1
                time.sleep(10*iPDP)
            else:
                stRead = self.write('AT+QIDEACT=1\r', ("OK", "ERROR"))
                stRead = self.write('AT+QIACT=1\r', ("OK", "ERROR"))
            iPDP = iPDP % 6

    def reInicializaAPN(self):
        self.printDebug('###  Reiniciando Conexion General        ###')
        #self.ser.write("+++\r\x1A\r")
        self.writeSer("\x1A\r")
        self.printDebug('###           Cerrando conexion  TCP      ###')
        stRead = self.write('AT+QICLOSE=0\r', ("OK", "ERROR"))
        self.printDebug('###           Cerrando conexion  APN      ###')
        stRead = self.write('AT+QIDEACT=1\r', ("OK", "ERROR"))
        self.write('ATE0\r',("OK","OK"))
        self.inicializaAPN()

    def inicializaTCP(self):
        cmd =  'AT+QIOPEN=1,0,"TCP","%s",%s,0,0\r' % (self.clDB.urlSocket, self.clDB.puertoSocket)
        self.parent.flSocket = False
        iTCP = 0 
        while (not self.parent.flSocket):
            stRead = self.write(cmd, ("QIOPEN", "ERROR"))
            #self.printDebug("QIOPEN: "+stRead)
            self.printDebug('### CONEXION TCP                          ### '+str(datetime.datetime.now().time()))
            if(stRead.find("QIOPEN: 0,0") != -1):
                self.printDebug('###                       CONEXION TCP OK ### '+str(datetime.datetime.now().time()))
                self.parent.flSocket = True
            else:
                if(stRead.find('562') != -1):
                    self.printDebug('###                           TCP ABIERTA ### '+str(datetime.datetime.now().time()))
                    self.parent.flSocket = True
                else:
                    self.printDebug('###                             ERROR TCP ### '+str(datetime.datetime.now().time()))
                    iTCP = (iTCP + 1) % 6
                    time.sleep(iTCP*10)

    def reInicializaTCP(self):
        self.printDebug('###           Cerrando conexion  TCP      ###')
        self.writeSer("\x1A\r")
        time.sleep(5)
        stRead = self.write('AT+QICLOSE=0\r', ("OK", "ERROR"))
        self.write('ATE0\r',("OK","OK"))
        self.inicializaTCP()

    def syncFecha(self):
        comando = ""
        while (not self.parent.flFecha):
            self.printDebug('###   Sincronizando Fecha con Proveedor   ###')
            stRead = self.write("AT+CCLK?\r",("OK","OK"))
            #self.printDebug("CCLK? "+stRead)
            i = stRead.find('"')
            #self.printDebug("Fecha: "+stRead[i+19:i+21])
            if (stRead != ""):
                try:
                    if (int(stRead[i+1:i+3]) > 17 and int(stRead[i+1:i+3]) < 50):
                        stFecha = "20"+stRead[i+1:i+3]+"-"+stRead[i+4:i+6]+"-"+stRead[i+7:i+9]+" "+stRead[i+10:i+18]
                        fecha = datetime.datetime(int("20"+stRead[i+1:i+3]), int(stRead[i+4:i+6]), int(stRead[i+7:i+9]), int(stRead[i+10:i+12]), int(stRead[i+13:i+15]), int(stRead[i+16:i+18])) - datetime.timedelta(hours=int(stRead[i+19:i+21])/4)
                        stFecha = fecha.strftime("%Y/%m/%d %H:%M:%S")
                        #self.printDebug("Fecha local: "+stFecha)
                        comando = 'sudo date --set "%s"'%str(stFecha)
                        #self.printDebug("comando"+comando)
                        self.parent.flFecha = True
                        self.printDebug('###  FECHA Proveedor '+stFecha)
                        self.stFecha = "RED"
                    else:        
                        self.printDebug('###                  No hay Servicio      ###')
                        self.printDebug('###   Sincronizando fecha con Servidor    ###')
                        i = 0
                        fecha = self.sendData("0,"+str(self.clDB.idUnidad))
                        if (fecha != ""):
                            fecha = " ".join(fecha.split()) #se le aplica un split al mismo comando
                            fecha = fecha.split(' ')
                            #self.printDebug("fecha: "+fecha)
                            stRead = "\""+fecha[2]+' '+fecha[3]+"\""
                            self.printDebug('###   Fecha Servidor '+stRead+'         ###')
                            comando = 'sudo date --set %s'%str(stRead)
                            self.parent.flFecha = True
                            self.stFecha = "SERVIDOR"
                            #self.parent.flRed = True
                            #self.parent.flFecha = True
                        else:
                            self.printDebug('###                  No hay Conexionv   ###')
                except:
                    self.printDebug("Error:"+stRead)
        if (comando != ""):
            os.system(comando)
            self.clDB.insertBitacora(stRead)

    def syncLog(self):
	self.printDebug('### Syncronizando LOG                     ###')
        stFile = "innobusmx/innobus.log"
        i = 0
        r = 0
        if os.path.exists(stFile):
            file=open(stFile,"r")
            st = file.readline()
            #self.printDebug("si existe:"+stFile)
            while (st != ""):
                stRead = self.sendData(st)
                i += 1
                if (stRead.find('QIRD:1=\r1\r')):
                    r += 1
                st = file.readline()
                #self.printDebug("send data: "+st)
            file.close()
            if (i == r):
                os.remove(stFile)

    def syncVersion(self):
        self.printDebug('### Sincronizando Versiones del Validador ###')
        dato = self.sendData("I,"+str(self.clDB.idUnidad)+","+self.parent.iccid+","+self.parent.serialNumber+","+self.parent.stVersion+","+self.parent.version+","+self.stFecha+","+self.stIP+","+str(self.clDB.economico))
        self.printDebug('###  Sincronizando Software con Servidor  ###')
        i = 0
        dato = self.sendData("S,0,"+str(self.clDB.idUnidad)+",Prepago")
        dato = " ".join(dato.split()) #se le aplica un split al mismo comando
        dato = dato.split('@')
        if (len(dato) > 2):
            self.parent.flFTP = True
            self.parent.lblNombreOperador.setText("Actualizando Software "+self.parent.stVersion)
            cmd =  'AT+QFTPOPEN="%s",%s\r' % (self.clDB.urlFTP, self.clDB.puertoFTP)
            stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"))
            self.printDebug('### CONEXION FTP                          ###')
            if(stRead.find("QFTPOPEN: 0,0") != -1) or (stRead.find('530') != -1):
                if(stRead.find('530') != -1):
                    self.printDebug('###                           FTP ABIERTA ###')
                else:
                    self.printDebug('###                       CONEXION FTP OK ###')
                if (self.descargarArchivoFTP(dato[2],dato[3], True)):
                    stRead = self.sendData("S,1,"+str(self.clDB.idUnidad)+","+dato[2])

                    if (dato[4] == "r"):
                        stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,1,0,0,0\r'
                        stGPS = self.sendData(stGPS)
                        self.reInitApp()
                    if (dato[4] == "R"):
                        stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,1,0,0,0\r'
                        stGPS = self.sendData(stGPS)
                        #self.printDebug("Reboot:"+dato[4])
                        os.system('sudo reboot')
                    if (dato[4] == "A"):
                        stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,1,0,0,0\r'
                        stGPS = self.sendData(stGPS)
                        self.serial.closeSerial()
                        os.system('avrdude -v -patmega328p -Uflash:w:/home/pi/'+dato[3]+':i -carduino -b 115200 -P '+self.serial.sPort)
                        os.remove(dato[3])
                        self.reInitApp()
                else:
                    self.printDebug('###              ERROR LEER ARCHIVOFTP ###')
            else:
                self.printDebug('###                             ERROR FTP ###')
            self.parent.lblNombreOperador.setText("")
            stRead = self.write("AT+QFTPCLOSE\r", ("QFTPCLOSE:", "ERROR"))
            self.parent.flFTP = False












                
    def senial3G(self):
        senial = 0
        stRead = self.write('AT+CSQ\r', ("OK", "ERROR"))
        #self.printDebug("CSQ: "+stRead)
        #self.printDebug("pos: "+stRead+" pos[10]: "+stRead[10])
        if (stRead.find("OK") != -1):
            i = stRead.find("+CSQ:")
            if (i != -1):
                i = 9
                if (stRead[10] == ","):
                    i = 10
                #self.printDebug("signal "+stRead[7:i])
                try:
                    senial = int(stRead[7:i])
                except:
                    self.printDebug("Error: Casting int() SignalQuality. "+stRead[7:i]+"  "+stRead)
                    self.write('ATE0\r',("OK","OK"))
                #self.printDebug("Senial ("+stRead[:i+8]+")"+senial)
                self.parent.iComm = senial
            else:
                self.printDebug("Error: Return SignalQuality. "+stRead)
                self.parent.iComm = 0
        else:
            self.printDebug("Error: SignalQuality. "+stRead)
            self.parent.iComm = 0

        return senial


        

    def sendData(self, data):
        self.lock = True
        result = ""
        senial = self.senial3G()
        #self.printDebug("Senial: "+str(senial))
        if senial > 5 and senial  != 99 and self.parent.flRed and self.parent.flSocket:
            stRead = self.write('AT+QISEND=0\r', ("ERROR", "OK", '>')) 
            if (stRead.find(">") != -1):
                cmd = data+"\r\x1A\r"
                stRead = self.write(cmd,('recv', 'ERROR'))
                if (stRead.find('"recv",0') != -1):
                    result = self.write('AT+QIRD=0\r', ("OK", "ERROR"))
                elif (stRead.find('ERROR') != -1) or (self.sendError == self.maxSendError):
                    self.reInicializaTCP()
                else:
                    self.sendError += 1
                    self.writeSer("\x1A\r")
            elif (stRead.find("ERROR") != -1):
                self.reInicializaTCP()
            else:
                self.writeSer("\x1A\r")
        else:
            #time.sleep(5)
            if not self.parent.flRed:
                self.printDebug("Error: No hay conexion de Red. PDP "+data)
            elif not self.parent.flSocket:
                self.printDebug("Error: No hay conexion con el Servidor TCP "+data)
            else:
                self.printDebug("Error: Bad SignalQuality. "+data)

        self.lock = False
        return result

    def gpsOn(self):
        stRead = self.write("AT+QGPS=1\r",("OK\r", "+CME ERROR"))
        if (stRead.find("OK") != -1):
            self.printDebug('###                                GPS OK ###')
            self.parent.flGPSOK = True
	else:
            if (stRead.find("504") != -1):
                self.printDebug('###                             El GPS ON ###')
                self.parent.flGPSOK = True
            else:
                self.printDebug('                          ERROR EN EL GPS ###')
        
    def gpsOff(self):
        self.printDebug('### Cerrando GPS                         ###')
        self.parent.flGPSOK = False
        stRead = self.write("AT+QGPSEND\r",("OK\r", "ERROR"))
        time.sleep(3)
        stRead = self.write("AT+QGPSDEL=0\r",("OK\r", "ERROR"))
        time.sleep(3)
        

    def obtenerCoordenadaGPS(self):
        stGPS = ""
        if self.flGetGPS:
            stRead = self.write('AT+QGPSLOC=2\r', ("OK", "ERROR"))
            self.parent.flGPS = (stRead.find("OK") != -1)
            if self.parent.flGPS:
                stRead = " ".join(stRead.split())
                my_list = stRead.split(",")
                # 0 Hora  (hh-mm-ss)
                # 1 latitud
                # 2 longitud
                # 7 velocidad
                # 9 Fecha (dd-mm-aa)
                if (len(my_list) == 11):
                    self.iNoGPS = 0
                    latitud = my_list[1]
                    longitud = my_list[2]
                    velGPS = my_list[7]
                    datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
                    idInser = my_list[9][0:2]+my_list[0][10:16]
                    self.idCons += 1
                    self.parent.lblVelocidad.setText(str(velGPS))
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
                                self.printDebug("error en el insert del GPS")
                else:
                    self.printDebug(str(my_list))
                    self.printDebug("###              Error> Lista mal formada ### ")
                        
            else:
                self.iNoGPS += 1
                #self.printDebug("iNoGPS ("+str(self.iNoGPS)+")"+stRead)
                #time.sleep(5)
                velGPS = 0
                self.parent.lblVelocidad.setText("-")
                if (self.iNoGPS == self.iMaxTryGPS):
                    #self.configuraGPS()
                    self.iNoGPS = 0
        if (stGPS == ""):
            stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,0,0,0,0\r'
            stGPS = self.sendData(stGPS)
        stGPS = ''.join(stGPS)
        stGPS = stGPS.split("\r\n")
        #self.printDebug("stGPS: ("+str(len(stGPS))+")"+stGPS)
        
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
                    stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,1,0,0,0\r'
                    stGPS = self.sendData(stGPS)
                    if self.syncVersion():
                        self.printDebug("")
                if (stGPS[1] == "g"):
                    stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,1,0,0,0\r'
                    stGPS = self.sendData(stGPS)
                    self.gpsOff()
                if (stGPS[1] == "G"):
                    stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,1,0,0,0\r'
                    stGPS = self.sendData(stGPS)
                    self.gpsOn()
                if (stGPS[1] == "9"):
                    self.descargarFotografia(stGPS[2])
                if (stGPS[1] == "e"):
                    self.printDebug("Error de Prueba")
                    stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,1,0,0,0\r'
                    stGPS = self.sendData(stGPS)
                    stGPS[1] = stErrordePrueba
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
                self.printDebug('###       Si hay Aforos nuevos      ###')
                stAforo = '3,'+str(data[1])+','+str(data[2])+','+str(data[3])+','+str(data[4])+','+str(data[5])+','+str(data[6])+','+str(data[8])+','+str(data[7])+'\r'+''
                self.printDebug('###      Dato a enviar en validacion      ###')
                #self.printDebug(stAforo)
                salgo = 0
                #self.procesoDeEnvio(validadorS, idValida, accion, salgo)
                stAforo = self.sendData(stAforo)
                if (stAforo != ""):
                    stAforo = ''.join(stAforo)
                    stAforo = stAforo.split("\r\n")
                    #self.printDebug("datos: ("+str(len(stAforo))+")"+stAforo)
                    if (len(stAforo) > 3):
                        #self.printDebug(str(len(stAforo))+"  stAforo: "+stAforo)
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


    def descargarArchivoFTP(self, origen, destino, msg):
        self.printDebug('###                       Inicia Descarga ###')
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
            self.printDebug(str(iLenFile)+"   "+origen)
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
                    #self.printDebug(stRead)
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
                        #self.printDebug("Leido: "+str(size))
                    else:
                        iError += 1
                        error = (iError == 10)
            if error:
                self.printDebug("Error ("+str(iError)+") "+ st)
                os.remove(destino+".tmp")
                return False
            else:
                if (destino.find(".zip") != -1):
                    self.printDebug('###                      Unzipping File   ###')
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
            self.printDebug("Error ("+stRead+")")
            return False
        
            
    def descargarFotografia(self, csn):
        self.printDebug('###                Descarga Fotografia ###')
        cmd =  'AT+QFTPOPEN="%s",%s\r' % (self.clDB.urlFTP, self.clDB.puertoFTP)
        stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"))
        self.printDebug('### CONEXION FTP                          ###')
        fl = False
        self.parent.flFTP = True
        if(stRead.find("QFTPOPEN: 0,0") != -1) or (stRead.find('530') != -1):
            if(stRead.find('530') != -1):
                self.printDebug('###                           FTP ABIERTA ###')
            else:
                self.printDebug('###                       CONEXION FTP OK ###')

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
            self.printDebug(str(sizeLocal)+"  "+str(iLenFile)+"   "+csn+".jpeg")
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
                            #self.printDebug("Leido: "+str(size))
                        else:
                            iError += 1
                            error = (iError == 10)
                if error:
                    self.printDebug("Error: ("+str(iError)+")")
                    os.remove(path+"/"+csn+".Jpeg.tmp")
                    fl = False
                else:
                    self.printDebug("Foto OK: "+csn+".Jpeg.")
                    os.rename(path+"/"+csn+".Jpeg.tmp", path+"/"+csn+".Jpeg")
                    fl = True
            else:
                self.printDebug("Foto Repetida: "+csn+".Jpeg.")
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
        #self.printDebug('### Lectura de mensajes ###')
        nSMS = 1
        comando = self.write("AT+CMGR=%s\r"%nSMS,("OK", "ERROR"))
        comandoS = comando.rstrip()
        comandoT = ",".join(comandoS.split())
        #self.printDebug('evaluo '+comandoT[0:6])
        if str(comandoT[0:6]) == '+CMGR:':
            text = comandoT.split(',')
            self.printDebug('Text '+text)
            try:
                cmd = text[8]
                #este pasa cuando hay una actualizacion por lo que
                #obtendre el comando sin la actualizacion
                if cmd[:2] == 'IU':
                    #self.printDebug('Actualizacion de algo')
                    strActualizacion = cmd
                    cmd = cmd[:6]
                    self.printDebug(strActualizacion)
                else:
                    #esto pasa cuando es un comando normal
                    cmd = text[8]
                    self.printDebug(cmd)
                    strActualizacion = 'nulo'
            except:
                self.printDebug('Mensaje sms no valido')
                cmd = 'ERROR'
                strActualizacion = 'nulo'
            self.validarComando(cmd, strActualizacion, nSMS)
            #self.printDebug('validar comando')
        nSMS = nSMS + 1
        #self.entrarAccionSiete = 0        

    def validarComando(self, comando, strActualizacion, sms):
        #comando = 'IREUC'
        
        if(comando.find("OK") != -1):
                comando = self.write("AT+CMGR=1\r",("OK", "ERROR"))                          
                self.printDebug('###  ###')
                i = comando.find("+CMGR:")
                j = comando.find("OK")                              
                comando=comando[i+56:j-4] 
        
        c= self.clDB.dbComando.cursor()
        self.printDebug("select validarComando")
        c.execute("SELECT comando, accion, dEjec FROM tComando WHERE comando = ?",(comando, ))
        self.printDebug("fetch validarComando")
        data = c.fetchone()
        self.printDebug(str(data))
        if data is None:
            self.printDebug('Comando no valido')
        else:
            comaT = data[0]
            acciT = data[1]
            dEjeT = data[2]
        #self.printDebug(execc)
        self.printDebug("close cursos validarComando")
        c.close()
        c = None

        if data is None:
            self.printDebug('###           Comando no soportado        ###')
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
                self.printDebug(str(return_code))
                #Elimino el comando SMS
                
                
            if dEjeT == 'o':
                self.printDebug(acciT)
                #Elimino el comando SMS
                cmd = 'AT+CMGD=%s\r'%str(sms)
                self.writeSer(cmd.encode())
                mensaje = self.readSer(128)
                
                
                
            if dEjeT == 'S':
                self.printDebug('Comando '+comando)
                self.printDebug('strComando '+strActualizacion)

                #self.printDebug("Connect comando accion")
                #connC = sqlite3.connect(cdDbC)
                self.printDebug("cursos comando accion")
                c= dbComando.cursor()
                self.printDebug("select comando accion")

                c.execute("SELECT accion FROM tComando WHERE comando = ?",(comando,))
                self.printDebug("fetch comando accion")
                datosComando = c.fetchone()
                self.printDebug("close comando accion")
                c.close()
                c = None
                if datosComando is None:
                    self.printDebug('No hay parametros de configuracon contacta al administrador')
                else:
                    accion = datosComando[0]

                self.printDebug( strActualizacion.split("@"))
                obtDatoActualizar =  strActualizacion.split("@")
                datoAActualizar = obtDatoActualizar[1]

                self.printDebug(accion.split(","))
                datosDeBase = accion.split(",")
                nombreTabla = str(datosDeBase[0])
                nombreRow = str(datosDeBase[1])
                nombreBase = str(datosDeBase[2])

                self.printDebug('Nueva pagina '+ datoAActualizar)
                self.printDebug('Donde lo voy a guardar '+ nombreTabla)
                self.printDebug('Nombre del campo a afectar '+ nombreRow)
                self.printDebug('Nombre de la base que voy a alterar '+ nombreBase)

                '''
                    Aca empieza el proceso de actualizacion de registro
                    esto va a funcionar para la actualizacion/sincronizacion
                    de los paramtros de configuracion del sistema
                '''
                
                self.printDebug("update data nombreBase")
                self.conn.execute('UPDATE ' +'"'+ nombreTabla +'"'+ ' set ' +'"'+ nombreRow +'"'+ ' = ?', (datoAActualizar, ))
                self.printDebug("commit data nombreBase")
                self.conn.commit()
                self.printDebug("close Connect data nombreBase")
               
                #Elimino el comando SMS
                cmd = 'AT+CMGD=%s\r'%str(sms)
                self.writeSer(cmd.encode())
                mensaje = self.readSer(128)

            else:
                self.printDebug('###          Comando no soportado         ###')
                cmd = 'AT+CMGD=%s\r'%str(sms)
                self.writeSer(cmd.encode())
                mensaje = self.readSer(128)

        

