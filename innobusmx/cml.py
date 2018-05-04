#!/usr/bin/python
# -*- coding: utf-8 -*-
#Hola

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
import os




#sPort = '/dev/ttyUSB1'
#velocidad = 115200
#ser = serial.Serial(sPort, velocidad, timeout=1)




class clQuectel(QtCore.QThread):
# Constantes
    maxSendError = 5
    
    idCons = 0
    lock = False
    sendError = 0
    qData = ()
    flFecha = False
    
    def __init__(self, parent, clDB, sPort3G, velocidad):
        self.idCons = 0
        QtCore.QThread.__init__(self)
        self.parent = parent
        self.clDB = clDB
        self.ser = serial.Serial(sPort3G, velocidad, timeout=1)        
        self.flG = False
        self.flR = True
        paso = 0

    def write(self, cmd, answer):
        #print "Tx >>>> ",cmd
        answer += ("closed",)
        stRead = ""
        self.ser.write(cmd.encode())
        find = False
        while not find:
            stRead += self.ser.readline()           
            for  j in answer:
                if ( stRead.find(j) != -1):
                    #print "Find: " + j
                    find = True
                    break
            #print stRead
        if (stRead.find("closed") != -1):
            self.reInicializaTCP()
        return stRead

    def run(self):
        print '#############################################'
        print '### Iniciando el modulo de comunicaciones ###'
        print '###                v0.02                  ###'
        print '#############################################'       

	print '###           Reiniciando MODEM           ###'
        self.write('AT+QPOWD=1\r',("RDY\r","RDY\r"))
	self.write('ATE0\r',("OK\r","OK\r"))
        time.sleep(5)
        ini = ''
        #self.suspender()
        self.inicializaGPS()
        self.validaSIM()
        self.inicializa3G()
        self.inicializaTCP()
        self.inicializaSMS()
        if (not self.flFecha):
            self.syncFecha()
        self.ajustesServicioFTP()
        self.loginServidorFTP()
        self.descargarArchivoFTP()
        print '#############################################'
        self.syncVersion()
        while True:
            self.obtenerCoordenadaGPS()
            time.sleep(1)
        
    def validaSIM(self):
        print '### VALIDAR MODULO SIM                    ###'
        stRead = self.write("AT+CPIN?\r",("OK","+CME ERROR"))
        #print "CPIN? "+stRead
        if(stRead.find("OK") != -1):
            print '###                         MODULO SIM OK ###'
            print '### VALIDAR REGISTRO SIM                  ###'
            stRead = self.write("AT+CREG?\r",("OK","ERROR"))
            #print "CREG? "+stRead
            if(stRead.find("+CREG: 0,1") != -1):
                print '###                    REGISTRO EN RED OK ###'
                stRead = self.write("AT+CCLK?\r",("OK","OK"))
                #print "CCLK? "+stRead
                i = stRead.find('"')
                #print "Fecha: ",int(stRead[i+19:i+21])
                if (int(stRead[i+1:i+3]) > 17 and int(stRead[i+1:i+3]) < 50):
                    stFecha = "20"+stRead[i+1:i+3]+"-"+stRead[i+4:i+6]+"-"+stRead[i+7:i+9]+" "+stRead[i+10:i+18]
                    fecha = datetime.datetime(int("20"+stRead[i+1:i+3]), int(stRead[i+4:i+6]), int(stRead[i+7:i+9]), int(stRead[i+10:i+12]), int(stRead[i+13:i+15]), int(stRead[i+16:i+18])) - datetime.timedelta(hours=int(stRead[i+19:i+21])/4)
                    stFecha = fecha.strftime("%Y/%m/%d %H:%M:%S")
                    #print "Fecha local: ",stFecha
                    comando = 'sudo date --set "%s"'%str(stFecha)
                    #print "comando",comando
                    os.system(comando)
                    self.flFecha = True
                    print '###  FECHA:',stFecha   
            else:
                print '###              FALLO DE REGISTRO EN RED ###'
	else:
            print '###                  ERROR EN TARJETA SIM ###'

    def inicializaGPS(self):
        print '### Iniciando GPS                         ###'
        stRead = self.write("AT+QGPS=1\r",("OK\r", "+CME ERROR"))
        #print "QGPS: "+stRead
        if (stRead.find("OK") != -1):
            print '###                                GPS OK ###'
            self.parent.flGPSOK = True
	else:
            if (stRead.find("504") != -1):
                print '###                             El GPS ON ###'
                self.parent.flGPSOK = True
            else:
                print '                          ERROR EN EL GPS ###'
                #print '###       GPS: '+stRead
                self.parent.flGPSOK = False

    def inicializaSMS(self):
        print '###                                       ###'
        print '### Configuracion SMS                     ###'
        stRead = self.write("AT+CMGF=1\r",("OK", "ERROR"))
        #print "CMGF: "+stRead
        if(stRead.find("OK") != -1):
            print '###                         MODULO SMS OK ###'
	else:
            print '###                   ERROR en Modulo SMS ###'

    def inicializa3G(self):
        statusPDP = 0
	print '###       INICIANDO CONEXION 3G           ###'
	print '### CONFIGURACION HTTP                    ###'
        stRead = self.write("AT+QHTTPCFG=\"contextid\",1\r", ("OK", "ERROR"))
        #print "AT+QHTTPCFG: "+stRead
        if (stRead.find("OK") == -1):
            print '###              FALLO AL CONFIGURAR HTTP ###'
        else:
            print '###                 CONFIGURACION HTTP OK ###'
            print '### VERIFICAR CONEXION PDP                ###'
            stRead = self.write("AT+QIACT?\r", ("OK","ERROR"))
            #print "AT+QIACT?: "+stRead
            if (stRead.find("ERROR") != -1):
                print '###            ERROR EN ACTIVACION DE PDP ###'
            elif (stRead.find("+QIACT: 1,1,1") != -1):
                print '                        Conx PDP Conf Ant ###'
                statusPDP = 2
            else:
                print '### CONFIGURAR PDP                        ###'
                cmd =   'AT+QICSGP=1,1,"%s","%s","%s",1\r' % (self.clDB.proveedorInternet, self.clDB.usuarioProveedor, self.clDB.passProveedor)
                stRead = self.write(cmd, ("OK", "ERROR"))
                #print "QICSGP: "+stRead
                stRead = " ".join(stRead.split())
                if (stRead.find("OK") == -1):
                    print '###               FALLO AL CONFIGURAR PDP ###'
                else:
                    print '###                  CONFIGURACION PDP OK ###'	    
                    stRead = self.write('AT+QIACT=1\r', ("OK", "ERROR"))
                    #print "AT+QIACT=1: "+stRead
                    if (stRead.find("OK") == -1):
                        print '###                  FALLO AL ACTIVAR PDP ###'
                    else:
                        print '###                     ACTIVACION PDP OK ###'

    def inicializaTCP(self):	
        cmd =  'AT+QIOPEN=1,0,"TCP","%s",%s,0,0\r' % (self.clDB.urlSocket, self.clDB.puertoSocket)
        stRead = self.write(cmd, ("QIOPEN: 0,0", "QIOPEN: 0,5", "ERROR"))
        #print "QIOPEN: "+stRead
        print '### CONEXION TCP                          ###'
        self.parent.flRedOK = True
        if(stRead.find("QIOPEN: 0,0") != -1):
            print '###                       CONEXION TCP OK ###'
            self.parent.flRedOK = True
        else:
            if(stRead.find('562') != -1):
                print '###                           TCP ABIERTA ###'
            else:
                self.parent.flRed = False
                print '###                             ERROR TCP ###'

    def reInicializaTCP(self):
        print '###           Cerrando conexion  TCP     ###'
        stRead = self.write('AT+QICLOSE=0\r', ("OK", "OK"))
        #print "QIDEACT: "+stRead
        if (stRead.find("OK") != -1):
            print '###       Reiniciando Conexion TCP       ###'
            self.inicializaTCP()

    def reInicializa3G(self):
        print '###           Desactivando conexion        ###'
        stRead = self.write('AT+QIDEACT=1\r', ("OK", "ERROR"))
        #print "QIDEACT: "+stRead
        if (stRead.find("OK") != -1):
            #print '###           Reiniciando MODEM          ###'
            #self.write('AT+QPOWD=1\r',("RDY", "RDY"))
            #print "AT+QRST: " +stRead
            self.inicializa3G()


    def sendData(self, data):

        self.lock = True
        result = ""
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
                    print "Error: Casting int() SignalQuality.", stRead[7:i]
                #print "Senial (",stRead[:i+8],")",senial
                if senial > 5 and senial  != 99:
                    stRead = self.write('AT+QISEND=0\r', ("ERROR", "OK", '>')) 
                    #print "QISEND (Hora): "+stRead
                    if (stRead.find(">") != -1):
                        cmd = data+"\r\x1A\r"
                        stRead = self.write(cmd,('recv', 'ERROR', 'closed'))
                        #print "send : (" + str(i) + ")" + stRead
                        if (stRead.find('"recv",0') != -1):
                            result = self.write('AT+QIRD=0\r', ("OK", "ERROR"))
                            #print "AT+QIRD=0: ", result
                        elif (stRead.find('closed') != -1):
                            print "Error: Conexion Cerrada "                        
                            self.reInicializaTCP()
                        elif (self.sendError == self.maxSendError):
                            self.reInicializa3G()
                        else:
                            self.sendError += 1
                    else:
                        print "Error: Send Data no > "
                        self.reInicializa3G()
                        self.reInicializaTCP()
                else:
                    print "Error: Bad SignalQuality.", stRead[i+5:i+8]                    
            else:
                print "Error: Return SignalQuality."
        else:
            print "Error: SignalQuality."
        self.lock = False
        return result

    
        
    def syncFecha(self):
        print '###   Sincronizando fecha con Servidor    ###'
        i = 0
        fecha = self.sendData("00")
        if (fecha != ""):
            fecha = " ".join(fecha.split()) #se le aplica un split al mismo comando
            fecha = fecha.split(' ')
            #print "fecha: ",fecha
            stRead = "\""+fecha[2]+' '+fecha[3]+"\""
            print '###   Fecha '+stRead+'         ###'
            comando = 'sudo date --set %s'%str(stRead)
            os.system(comando)
            self.parent.flRed = True
            self.parent.flFecha = True
            self.clDB.insertBitacora(stRead)

    def syncVersion(self):
        print '###  Sincronizando Software con Servidor  ###'
        i = 0
        print "Sync:","S,0,"+str(self.clDB.idUnidad)+",Prepago"
        dato = self.sendData("S,"+str(self.clDB.idUnidad)+",Prepago")
        if (len(dato) > 1):
            dato = " ".join(dato.split()) #se le aplica un split al mismo comando
            dato = dato.split('@')
            print "dato: ",dato 

            

    def obtenerCoordenadaGPS(self):
        '''
            ##############################################################
                Modulo que obteniene la coordenada GPS la guarda cuando
                el GPS se establece de manera correcta.
            ##############################################################
        '''
        #self.parent.noGPS.setPixmap(QtGui.QPixmap(""))
        #self.parent.lblMsg.setText("o")
        stRead = self.write('AT+QGPSLOC=0\r', ("OK", "ERROR", "closed")) 
        #print "QGPSLOC: "+stRead
        #self.parent.lblMsg1.setText("QGPSLOC: "+stRead)
        #time.sleep(2)
        self.parent.flGPS = (stRead.find("OK") != -1)
        if(self.parent.flGPS):
                self.parent.flGPS = True
                self.parent.flComm = True
#            try:
#                self.noGPS.setPixmap(QtGui.QPixmap(""))
		stRead = " ".join(stRead.split()) #se le aplica un split al mismo comando
		my_list = stRead.split(",")
                # 0 Hora  (hh-mm-ss)
		# 1 latitud
		# 2 longitud
                # 7 velocidad
                # 9 Fecha (dd-mm-aa)
                #print my_list
                if (len(my_list) == 11):
                    hora = my_list[0][10:12] + ":" + my_list[0][12:14] + ":" + my_list[0][14:16]
                    latitud = my_list[1][0:-1]
                    if (my_list[1][-1:] == 'S'):
                        latitud = '-' + latitud
                    longitud = my_list[2][0:-1]
                    velGPS = my_list[7]
                    #fecha = my_list[9][0:2] + "-" + my_list[9][2:4] + "-20" + my_list[9][4:6]
                    fecha = "20"+my_list[9][4:6] + "-" + my_list[9][2:4] + "-" + my_list[9][0:2]
                    idInser = my_list[9][0:2]+my_list[0][10:16]
                    l = float(latitud[0:2]) + (float(latitud[2:])/60)
                    latitud = ("%.6f" % l)
                    l = float(longitud[0:3]) + (float(longitud[3:])/60)
                    longitud = ("%.6f" % l)
                    if (my_list[2][-1:] == 'W'):
                        longitud = '-' + longitud
                    self.idCons += 1
                    self.parent.lblVelocidad.setText(str(velGPS))
                    if (self.parent.flComm):
                        datetimes = fecha + ' ' + hora
                        stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(datetimes)+','+str(latitud)+','+str(longitud)+','+str(velGPS)+','+str(self.idCons)+'\r'+''
                        #print "GPS (envio) " + stGPS
                        #self.parent.procesoDeEnvio(gpr, idInser, 1, 0)
                        stGPS = self.sendData(stGPS)
                        if stGPS == "":
                            #print '###         Dato valido insertandolo      ###'
                            #print "Connect insertando dato GPS"  
                            #print "Insert GPS"
                            fl = True
                            while fl:
                                try:
                                    #print "insert"
                                    self.clDB.dbGPS.execute('INSERT INTO tgps (hora, latitud, longitud, fecha, velocidad, idPos, enviado, idCons) VALUES (?, ?, ?, ?, ?, ?, 0, ?)', (hora, latitud, longitud, fecha, velGPS, idInser, self.idCons))
                                    self.clDB.dbGPS.commit()
                                    fl = False
                                except:
                                    fl = False
                                    print "error en el insert del GPS"
                        #else:
                            #print "GPS Ret: ",stGPS
                            #GPS Ret: +QIRD: 19 1@9@045534C2094F80@

                else:
                    print "###              Error> Lista mal formada ### "
 #           except:
 #                print '###   GPS fallo el parseo del dato   ###'
        else:
            if (stRead.find('closed') != -1):
                self.flRedOK = False
                self.flRed = False
                print '###           Error no existe conexion 3G ###'                
            else:
                velGPS = 0
                self.parent.lblVelocidad.setText("-")
                self.parent.flGPS = False
                print '###         Error al obtener Posicion GPS ###'                
        if (self.parent.flComm):
            #print '***     Verificando Aforo   ***'
            c = self.clDB.dbAforo.cursor()
            c.execute(" SELECT idValidador, idTipoTisc, idUnidad, idOperador, csn, saldo, tarifa, fechaHora, folios, enviado FROM validador WHERE enviado = 0 ORDER BY idValidador LIMIT 1")
            data = c.fetchone()
            if not (data is None):
                print '###       Si hay Aforos nuevos      ###'
                stAforo = '3,'+str(data[1])+','+str(data[2])+','+str(data[3])+','+str(data[4])+','+str(data[5])+','+str(data[6])+','+str(data[8])+','+str(data[7])+'\r'+''
                print '###      Dato a enviar en validacion      ###'
                print(stAforo)
                salgo = 0
                #self.procesoDeEnvio(validadorS, idValida, accion, salgo)
                stAforo = self.sendData(stAforo)
                print "stAforo: ",stAforo
                if stAforo != "":
                    self.clDB.dbAforo.execute('DELETE FROM validador WHERE idValidador = '+str(data[0]))
                    self.clDB.dbAforo.commit()
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
    
    
    



 
    

    def ajustesServicioFTP(self):
         
         cmd ='AT+QFTPCFG="account","Sistemas3","InnovaSis2017"\r'
         #cmd ='AT+QFTPCFG="transmode,1\r'
         stRead = self.write(cmd, ("OK", "ERROR"))
         if(stRead.find("OK") != -1):
               stRead = self.write('AT+QFTPCFG="filetype",0\r"',("OK","+CME ERROR"))  
               print '###            AJUSTES FTP OK             ###'
	 else:
               print '###            ERROR AJUSTES FTP      ###'
               
    def loginServidorFTP(self):
    
        #cmd =  'AT+QFTPOPEN="%s","%s"\r' % (self.clDB.urlSocket, self.clDB.puertoSocket)
        cmd =  'AT+QFTPOPEN="innovaslp.dyndns.org",21\r'
        stRead = self.write(cmd, ("QFTPOPEN: 0,0", "QFTPOPEN: 0,5", "ERROR"))
        #print "QFTPOPEN: "+stRead
        print '### CONEXION FTP                          ###'
        #self.parent.flRedOK = True
        if(stRead.find("QFTPOPEN: 0,0") != -1):
                print '###                       CONEXION FTP OK ###'
                #self.parent.flRedOK = True
                #stRead = self.write('AT+QFTCWD="/SincronizarValidadores/"', ("QFTPOPEN: 0,0", "QFTPOPEN: 0,5", "ERROR"))
        else:
                if(stRead.find('530') != -1):
                    print '###                           FTP ABIERTA ###'
                else:
                    self.parent.flRed = False
                    print '###                             ERROR FTP ###'



    def descargarArchivoFTP(self):
     print '###                       Descarga FTP OK ###'
     
     
     filtro='zip'
     origen = 'ftp.%s'%(filtro)
     #destino = 'ftp.%s'%(filtro)
   
    

    
     cmd = 'AT+QFTPGET="%s","COM:ftp.txt"\r'%str(origen)
   
     #stRead= StringIO.StringIO()
     #stRead=bytearray(10000000)
     
  
     stRead = ''      
     stRead = stRead + self.ser.read(self.ser.inWaiting())
     lines = stRead.split('\n') # Guaranteed to have at least 2 entries   
     stRead = lines[-1]
     #time.sleep(5)
     stRead = self.write(cmd,("+QFTPGET:0","CME ERROR" ))
     print '###                       Proceso de guardado ###'
     #time.sleep(8)
    

     if(stRead.find("OK") != -1):
                  
       print '###                      Inniciando comparticion de archivos ###'
       i = stRead.find("CONNECT")
       j = stRead.find("+QFTPGET")
       
       stRead=stRead[i+9:j-8]
       #print stRead
       #''' 
       encode=base64.b64encode(stRead) 

      
       
       imgdata = base64.b64decode(encode)
       with open('ftp.zip', 'wb') as f:
       #with open(destino, 'wb') as f:
          #imgdata.seek(0)
          f.write(imgdata)
        
       zip_ref=zipfile.ZipFile('ftp.zip','r')
       zip_ref.extractall('/home/pi/innobusmx')
       zip_ref.close()
       os.remove("ftp.zip")
      
    
       #descomentar para probar guardado de txt
       #archivo=open("actualiza.sh","w")
       #archivo.write(str(stRead[i+7:j-6]))
       #archivo.close()

        
       if (stRead.find("actualiza.sh") != -1):
           print 'Comprobacion de archivo sql para actualizacion de tabla' 
           os.system("chmod u+x actualiza.sh")
           os.system("sh actualiza.sh")
       
     else:
       print '###                              El NOMBRE DEL ARCHIVO ESTA INCORRECTO  ###'
              


    #def cerrarFTP(self):

     #cmd='AT+QFTPCLOSE \r'
     #stRead=self.write(cmd,("+QFTPCLOSE:0,0","CME ERROR" ))
      # print '###                              El NOMBRE DEL ARCHIVO ESTA INCORRECTO  ###'


    
    '''  
    def runner(self):
        #print "Obtener coordenada GPS"
        
        self.obtenerCoordenadaGPS()
        if (self.parent.flGPSOK):
            if (self.flG):
                if (self.parent.flGPS):
                    self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/GPS.png"))
                else:
                    self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noGPS.png"))
                self.flG = False
            else:
                self.parent.noGPS.setPixmap(QtGui.QPixmap(""))
                self.flG = True

        if (self.parent.flRedOK):
            if (self.flR):
                if (self.parent.flRed):
                    self.parent.noRed.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/3G.png"))
                else:
                    self.parent.noRed.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/no3G.png"))
                    self.inicializa3G() 
                self.flR = False
            else:
                self.parent.noRed.setPixmap(QtGui.QPixmap(""))
                self.flR = True
        else:
            self.reInicializa3G() 
        QtCore.QTimer.singleShot(1000, self.seguir)
    '''

