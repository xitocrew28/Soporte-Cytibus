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
#sys.path.insert(0, '/home/pi/innobusmx/src/')
#from func import funciones
#from rwdux3G import rwsGPS


class mainWin(QtGui.QMainWindow):
    def __init__(self):
        super(mainWin, self).__init__()
        self.dir = os.path.dirname(__file__)
        #self.cdDb = os.path.join(self.dir, 'data/db/tarifas')
        #self.openDBAforo = os.path.join(self.dir,'data/db/aforo')
        #self.openDBFotos = os.path.join(self.dir,'data/db/existeFoto')
        #self.openDBEV2 = os.path.join(self.dir,'data/db/ev2')
        #Definicion de variables globales
        self.retardo = 1
        self.intervaloTiempoParaInFin = 5
        self.nVuelta = 0

        self.velocidad = 115200
        self.sPort = ''
        self.sPort3G = ''     

        if self.sPort == '':
            path = "/dev"
            listdir = os.listdir(path)
            for file in listdir:
                if (file[0:6] == "ttyUSB"):
                    s = serial.Serial("/dev/"+file,self.velocidad, timeout=1)
                    s.flushInput()
                    s.flushOutput()
                    s.write("AT\r")
                    st = "."
                    while (st[-2:] != "AT") and (st != ""):
                        if (st == "."):
                            st = ""
                        st += str(s.read(1))
                    s.close
                    if (st == ""):
                        self.sPort = "/dev/"+file
                    if (st == "AT"):
                        self.sPort3G = "/dev/"+file
                
        print "RFID: "+self.sPort
        print "3G:"+self.sPort3G


        self.inicioFinUno = 'empezando'
        self.inicioFinActual = 'empezando'
        self.banderaIngreso  = 1
        self.valoresCard = {}
        self.versionOS = '0.10'
        self.turnoIniciadoFlag = False
        self.ser = serial.Serial(self.sPort3G, self.velocidad, timeout=1)
        self.connT = sqlite3.connect('/home/pi/innobusmx/data/db/gps')
        self.conn = sqlite3.connect('/home/pi/innobusmx/data/db/aforo')

        self.initUI()
        self.modem = inicioGPS(self, self.ser, self.flGPS, self.noGPS, self.connT, self.conn)
        self.hora = reloj(self, self.ser, self.modem, self.connT, self.conn)

##        self.funcCore = funciones(self)
##        self.funcCore.datosVuelta        

##        self.esS = escucharSerial(self, self.funcCore)
##        self.esS.daemon = True
##        self.connect(self.esS, self.esS.signal, self.funcCore.mostrarFoto)
##        self.connect(self.esS, self.esS.signal2, self.funcCore.borrarFoto)
##        self.esS.start()
        
##        self.obj = rwsGPS(self)
##        self.modem.daemon = True
##        self.modem.start()

    def initUI(self):

        self.reinicioAutomatico = 0
        self.idCons = 0
        self.idTransportista = 0
        self.idUnidad = 0
        self.logo = QtGui.QLabel(self)
        self.logo.setScaledContents(True)
        pathImgFondo = os.path.join(self.dir,'data/img/wall2.bmp')
        self.logo.setPixmap(QtGui.QPixmap(pathImgFondo))
        self.logo.move(0, 0)
        self.logo.resize(800, 480)

        self.lblOperador = QtGui.QLabel(self)
        self.lblOperador.setScaledContents(True)
#        pathChofer = os.path.join(self.dir,'')
#        self.lblOperador.setPixmap(QtGui.QPixmap(pathChofer))
        self.lblOperador.move(30, 120)
        self.lblOperador.resize(243, 320)

        self.lblUnidad = QtGui.QLabel('', self)
        self.lblUnidad.resize(self.width(), 50)
        self.lblUnidad.move(400, 170)
        self.lblUnidad.setStyleSheet('QLabel { font-size: 40pt; font-family: \
            Arial; color:Ref}')
#        self.lblUnidad.setText("52")

        self.lblNombreOperador = QtGui.QLabel('', self)
        self.lblNombreOperador.resize(self.width(), 50)
        self.lblNombreOperador.move(400, 370)
        self.lblNombreOperador.setStyleSheet('QLabel { font-size: 35pt; font-family: \
            Arial; color:Green}')

        self.lblRuta = QtGui.QLabel('', self)
        self.lblRuta.resize(self.width(), 50)
        self.lblRuta.move(400, 270)
        self.lblRuta.setStyleSheet('QLabel { font-size: 35pt; font-family: \
            Arial; color:Green}')

        self.lblVuelta = QtGui.QLabel('', self)
        self.lblVuelta.resize(self.width(), 50)
        self.lblVuelta.move(670, 170)
        self.lblVuelta.setStyleSheet('QLabel { font-size: 35pt; font-family: \
            Arial; color:Black}')

        self.lblVelocidad = QtGui.QLabel('', self)
        self.lblVelocidad.resize(self.width(), 50)
        self.lblVelocidad.move(670, 270)
        self.lblVelocidad.setStyleSheet('QLabel { font-size: 35pt; font-family: \
            Arial; color:Black}')

        conn = sqlite3.connect('/home/pi/innobusmx/data/db/aforo')
        c = conn.cursor()
        c.execute("SELECT nunEco, Operador FROM configuraSistema")
        data = c.fetchone()
        if data is None:
            self.lblUnidad.setText("")
            self.lblNombreOperador.setText("")
        else:
            self.lblUnidad.setText(str(data[0]))
            self.lblNombreOperador.setText(data[1])
        c.execute('select fechaHora, ruta.nombre, csn, num_vuelta, tTurno.nombre, inicioFin from soloVuelta, ruta, tTurno WHERE soloVuelta.idRuta = ruta.Id AND soloVuelta.turno = tTurno.idTurno ORDER BY idSoloVuelta DESC LIMIT 1')
        data = c.fetchone()
        c.close()
        if (data is None) or (data[5] == "F"):
            self.lblOperador.setPixmap(QtGui.QPixmap(""))
            self.lblRuta.setText("")
            self.lblNombreOperador.setText("")
            self.lblVuelta.setText("")
        else:
            self.lblRuta.setText(data[1])
            imgChofer = "data/user/%s.Jpeg"%data[2]
            scriptChofer = os.path.join(self.dir, imgChofer)
            self.lblOperador.setPixmap(QtGui.QPixmap(scriptChofer))
            self.lblVuelta.setText(str(data[3]))
        conn.close

        self.lblHora = QtGui.QLabel('', self)
        self.lblHora.resize(self.width(), 50)
        self.lblHora.move(10, 440)
        self.lblHora.setStyleSheet('QLabel { font-size: 14pt; font-family: \
            Arial; color:White}')

        self.lblMsg = QtGui.QLabel('', self)
        self.lblMsg.resize(self.width(), 50)
        self.lblMsg.move(10, 380)
        self.lblMsg.setStyleSheet('QLabel { font-size: 8pt; font-family: \
            Arial; color:Blue}')

        self.lblMsg1 = QtGui.QLabel('', self)
        self.lblMsg1.resize(self.width(), 50)
        self.lblMsg1.move(10, 340)
        self.lblMsg1.setStyleSheet('QLabel { font-size: 8pt; font-family: \
            Arial; color:Blue}')

        self.msg = QtGui.QLabel('', self)
        self.msg.resize(self.width(), 50)
        self.msg.move(135, 400)
        self.msg.setStyleSheet('QLabel { font-size: 30pt; font-family: \
            Arial; color:red}')

        '''
            ############################################################
                Aqui estan las variables que necesito para mostrar
                        la informacion de los aforo
            ############################################################
        '''

        self.lblAlteTurno = QtGui.QLabel('', self)
        self.lblAlteTurno.resize(self.width(), 50)
        self.lblAlteTurno.move(200, 360)
        self.lblAlteTurno.setStyleSheet('QLabel { font-size: 25pt; font-family: \
            Arial; color:white}')


        self.lblAlteTurnoDos = QtGui.QLabel('', self)
        self.lblAlteTurnoDos.resize(self.width(), 50)
        self.lblAlteTurnoDos.move(200, 400)
        self.lblAlteTurnoDos.setStyleSheet('QLabel { font-size: 25pt; font-family: \
            Arial; color:white}')


        imgTarjetaAtras = "data/img/imgTarjetas/CD.jpg"
        imgUsuarioTarjeta = "data/user/admin.Jpeg"

        self.imgTarjeta = QtGui.QLabel(self)
        self.imgTarjeta.setPixmap(QtGui.QPixmap(""))
        #self.imgTarjeta.setPixmap(QtGui.QPixmap(imgTarjetaAtras))
        self.imgTarjeta.setScaledContents(True)
        self.imgTarjeta.move(0,0)
        self.imgTarjeta.resize(800, 480)

        self.noRed = QtGui.QLabel(self)
        #self.noRed.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noRed.Jpeg"))
        self.noRed.setScaledContents(True)
        self.noRed.move(770,425)
        self.noRed.resize(20, 20)

        self.flRed = False
        self.flRedOK = False

        self.noGPS = QtGui.QLabel(self)
        #self.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noGPSEncendido.png"))
        self.noGPS.setScaledContents(True)
        self.noGPS.move(740,425)
        self.noGPS.resize(20, 20)

        self.flGPS = False
        self.flGPSOK = False

        self.noRDIF = QtGui.QLabel(self)
        if self.sPort == '':
            self.noRDIF.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noRFID.Jpeg"))
        else:
            self.noRDIF.setPixmap(QtGui.QPixmap(""))
        self.noRDIF.setScaledContents(True)
        self.noRDIF.move(710,425)
        self.noRDIF.resize(20, 20)

        self.noSevidor = QtGui.QLabel(self)
        #self.noSevidor.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noServidor.Jpeg"))
        self.noSevidor.setScaledContents(True)
        self.noSevidor.move(680,425)
        self.noSevidor.resize(20, 20)


        self.imgDefault = QtGui.QLabel(self)
        self.imgDefault.setPixmap(QtGui.QPixmap(""))
        self.imgDefault.setScaledContents(True)
        self.imgDefault.move(0,0)
        self.imgDefault.resize(480,480)
        #antigui tamano
        #self.imgDefault.resize(335,345)

        self.lblNombreApe = QtGui.QLabel('', self)
        self.lblNombreApe.resize(self.width(), 50)
        self.lblNombreApe.move(100, 400)
        self.lblNombreApe.setStyleSheet('QLabel { font-size: 50pt; font-family: \
            Arial; color:black}')

        self.lblSaldo = QtGui.QLabel('', self)
        self.lblSaldo.resize(self.width(), 75)
        #antiguo
        self.lblSaldo.move(480, 260)
        #self.lblSaldo.move(400, 300)
        self.lblSaldo.setStyleSheet('QLabel { font-size: 55pt; font-family: \
            Arial; color:Green}')
            #E6F9AF
        #self.lblNombreApe.hide()

        self.lblSS = QtGui.QLabel('', self)
        self.lblSS.resize(self.width(), 50)
        self.lblSS.move(270, 45)
        self.lblSS.setStyleSheet('QLabel { font-size: 45pt; font-family: \
            Arial; color:White}')
            ##8BBEB2

        self.lblVAI = QtGui.QLabel('', self)
        self.lblVAI.resize(self.width(), 50)
        self.lblVAI.move(150, 45)
        self.lblVAI.setStyleSheet('QLabel { font-size: 50pt; font-family: \
            Arial; color:White}')

        self.lblSSMsg = QtGui.QLabel('', self)
        self.lblSSMsg.resize(self.width(), 50)
        self.lblSSMsg.move(150, 350)
        self.lblSSMsg.setStyleSheet('QLabel { font-size: 45pt; font-family: \
            Arial; color:White}')

        self.lblTarjetas = QtGui.QLabel('', self)
        self.lblTarjetas.resize(self.width(), 50)
        self.lblTarjetas.move(180, 220)
        self.lblTarjetas.setStyleSheet('QLabel { font-size: 30pt; font-family: \
            Arial; color:Yellow}')

        self.lblNV = QtGui.QLabel('', self)
        self.lblNV.resize(self.width(), 50)
        self.lblNV.move(265, 45)
        self.lblNV.setStyleSheet('QLabel { font-size: 45pt; font-family: \
            Arial; color:White}')

        self.lblInFinVuelta = QtGui.QLabel('', self)
        self.lblInFinVuelta.resize(self.width(), 50)
        self.lblInFinVuelta.move(200, 220)
        self.lblInFinVuelta.setStyleSheet('QLabel { font-size: 40pt; font-family: \
            Arial; color:red}')

        self.setGeometry(-1, 0, 800, 480)
        self.setWindowTitle('InnoBusMx v0.2')
        self.setStyleSheet('''QMainWindow { background-color:#1D2556;}
            QLabel{font-size: 15pt; font-family: Courier; color:black;
            font-weight: bold}''')
            #18314F
        #self.showMaximized()
        #self.setWindowFlags(QtCore.Qt.CustomizeWindowHint)
        #self.showFullScreen()
        self.center()
        self.show()


    def center(self):
        frameGm = self.frameGeometry()
        centerPoint = QtGui.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())


    def procesoDeEnvio(self, dato, idActualizar, accion, salgo):
        print '###       Proceso de envio de datos       ###'
        salirEnvio = 0
        self.evento = accion

        while(salgo != 1):
            #print 'Cuanto vale', salirEnvio
            #print "Dato: "+dato
            cmd = 'AT+QISEND=0\r'
            self.ser.write(cmd.encode())
            stRead = ""
            i=0
            while (i < 1024) and (stRead[-5:] != "ERROR") and (stRead[-9:] != "SEND FAIL") and (stRead[-7:] != 'SEND OK') and (stRead[-1:] != ">"):
                stRead += str(self.ser.read(1))
                i += 1
            print "QISEND (Dato " + str(i) + "): "+stRead

            if (stRead[-1:] == ">"):
#                self.noRed.setPixmap(QtGui.QPixmap(""))
                self.ser.write(dato.encode()+"\x1A")
                stRead = ""
                while (stRead[-8:] != '"recv",0') and (stRead[-5:] != "ERROR") and (stRead[-10:] != '"closed",0'):
                    stRead += str(self.ser.read(1))                    
                print "send dato: "+stRead
                    
                if (stRead[-8:] == '"recv",0'):
    		    cmd = 'AT+QIRD=0\r'
                    self.ser.write(cmd.encode())
                    stRead = ""
                    while (stRead[-2:] != 'OK') and (stRead[-5:] != 'ERROR'):
                        stRead += str(self.ser.read(1))
                    #print "QIRD: "+stRead
		    stRead = " ".join(stRead.split()) #se le aplica un split al mismo comando
                    print "QIRDs: "+stRead

                    if (stRead[-2:] == 'OK'):
                        self.flRed = True
                        lista = stRead.split(' ')
                        #print "Lista "
                        #print lista
                        if (lista[2] == "0"):
                            print '###         No hay Datos que leer         ###'
                        else:
                            if (lista[3][0] == "1"):
                                salgo = 1
                                enviado = 1
                                #buscar si hay una posible actualizacion
                                if (lista[3].find('@') != -1):
                                    #print 'encontre una actualizacion'
                                    #print lista[3]
                                    try:
                                        #print lista[3].split("@")
                                        dos = lista[3].split("@")
                                        #print dos[1]
                                        #print dos[2]
                                        self.actualizarAlgo = lista[3]
                                    except:
                                        print 'No pude parsear la actualizacion'
                                #else:
                                    #print 'no encontre nada que hacer'
                            else:
                                #print 'No recibi un numero osea que esta fallando la comun'
                                #print salirEnvio
                                salirEnvio += 1
                                if (salirEnvio == 2):
                                    #print 'Si es mayor entonces rompo el scrip'
                                    self.reinicioAutomatico = self.reinicioAutomatico + 1
                                    salgo = 1
                                    enviado = 0
                    else:
                        self.flRed = False                
                else:
                    self.flRed = False
#                    self.noRed.setPixmap(QtGui.QPixmap("data/img/noRed.Jpeg"))
                    print '###  Error Recepcion Datos Servidor      ###'
            else:
                self.flRed = False
#                self.noRed.setPixmap(QtGui.QPixmap("data/img/noRed.Jpeg"))
                print '###   Error Conexion con el Servidor     ###'
                salgo = 1
                enviado = 0
        if(enviado == 1 and int(self.evento)==1):
            #print '###          Actualizando GPS            ###'
            #print "Connect actualizando GPS"  
            #connT = sqlite3.connect(cdDbT)
            #c = conn.cursor()
            #connT.execute("UPDATE tgps SET enviado = 1 WHERE idPos = ?", (idActualizar,))
            print "delete actualizando GPS"  
            self.connT.execute("DELETE FROM tgps WHERE idPos = ?", (idActualizar,))
	    #print "idActualizar "+idActualizar
            print "commit actualizando GPS"  
            self.connT.commit()
            #c.close()
            #print "close Connect actualizando GPS"  
            #connT.close()
            #connT = None
            self.reinicioAutomatico = 0
        # Barras




class reloj():
    
    def __init__(self, parent, ser, modem, connT, conn):
        self.parent = parent
        self.flG = False
        self.flR = True
        self.ser = ser
        self.connT = connT
        self.conn = conn
#        self.ser = serial.Serial(self.parent.sPort3G, self.parent.velocidad, timeout=1)
#        self.connT = sqlite3.connect('/home/pi/innobusmx/data/db/gps')
#        self.conn = sqlite3.connect('/home/pi/innobusmx/data/db/aforo')
        self.inicializarTodo()
        self.mes=["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        self.mostrarHora()

    def inicializaGPS(self):
        print '###             Iniciando GPS             ###'
        cmd = "AT+QGPS=1\r"
        self.ser.write(cmd.encode())
        stRead = ""
        while (stRead[-2:] != "OK") and not ((stRead[-3:] >= "501") and (stRead[-3:] <= "549")):
            stRead += str(self.ser.read(1))
        #print "QGPS: "+stRead

        if (stRead[-2:] == "OK"):
            print '###       El GPS OK                       ###'
            self.parent.flGPSOK = True
	else:
            if (stRead[-3:] == "504"):
                print '###       El GPS ya esta encendido        ###'
                self.parent.flGPSOK = True
            else:
                print '###       Hay un problema con el GPS      ###'
                print '###       GPS: '+stRead
                self.parent.flGPSOK = False

    def inicializaMSG(self):
        print '###           Configuracion SMS           ###'
        cmd = "AT+CMGF=1\r"
        self.ser.write(cmd.encode())
	stRead = ""
	while (stRead[-2:] != "OK") and (stRead[-5:] != "ERROR"):
            stRead += str(self.ser.read(1))
	#print "CMGF: "+stRead
        if(stRead[-2:] == "OK"):
            print '###               MODULO SMS OK           ###'
	else:
            print '###          ERROR en Modulo SMS          ###'

    def inicializa3G(self):
	print '###           Reiniciando conexion        ###'
	cmd = 'AT+QIDEACT=1\r'
	self.ser.write(cmd.encode())
	stRead = ""
	while (stRead[-2:] != "OK") and (stRead[-5:] != "ERROR"):
            stRead += str(self.ser.read(1))
	print "QIDEACT: "+stRead
		
	cmd = 'AT+QIACT?\r'
	stRead = ""
	while (stRead[-2:] != "OK"):
            self.ser.write(cmd.encode())
            stRead = ""
            while (stRead[-2:] != "OK") and (stRead[-5:] != "ERROR"):
                stRead += str(self.ser.read(1))
            #print "QIACT? "+stRead

#	cmd = 'AT+QIACT?\r'
#        self.ser.write(cmd.encode())
#        stRead = ""
#        while (stRead[-2:] != "OK") and (stRead[-5:] != "ERROR"):
#            stRead += str(self.ser.read(1))
            
        #stRead = " ".join(stRead.split())
        #print "QIACT? "+stRead
        
	print '###           Verificando Status          ###'
	if(stRead[-5:] == "ERROR"):
	    print '###               ERROR  Status           ###'
	    self.ser.write("\x1A")
        else:            
            if(stRead[:23] == 'AT+QIACT? +QIACT: 1,1,1'):
                print '###            Status correcto            ###'
            else:
                print '### Conectandome a la red 3G del provedor ###'
                csttS = 'AT+QICSGP=1,1,"%s","%s","%s",1 OK' % (self.provedor, self.usuarioProvedor, self.passProvedor)
                cmd =   'AT+QICSGP=1,1,"%s","%s","%s",1\r' % (self.provedor, self.usuarioProvedor, self.passProvedor)
                self.ser.write(cmd.encode())
		#print "Dato: "+dato
            	#self.ser.write(cmd.encode())
            	stRead = ""
		while (stRead[-2:] != "OK") and (stRead[-5:] != "ERROR"):
                    stRead += str(self.ser.read(1))
                #print "QICSGP: "+stRead
                #stRead = self.ser.read(96)
                stRead = " ".join(stRead.split())
                if(stRead != csttS):
                    print '###            Conexion 3G OK.           ###'
                else:
                    print '###            Conexion exitosa.          ###'	    
                    cmd = 'AT+QIACT=1\r'
                    self.ser.write(cmd.encode())
                    stRead = ""
                    while (stRead[-2:] != "OK") and (stRead[-5:] != "ERROR"):
                        stRead += str(self.ser.read(1))
                    #print "QIACT=1 "+stRead
					
                    print '###              Activa el PDP            ###'
                    if(stRead[-2:] == "OK"):
			print '###            Conexion exitosa.          ###'	    
                    else:
                        print '###        Error al activar el PDP        ###'
	
#	cipstartS = 'AT+QIOPEN=1,0,"TCP","innovacion.no-ip.org",10000,0,0 OK'
	cmd =  'AT+QIOPEN=1,0,"TCP","innovaciones.no-ip.org",10000,0,0\r' 
	self.ser.write(cmd.encode())
	stRead = ""
	while (stRead[-9:] != "OPEN: 0,0") and not ((stRead[-3:] > "551" and stRead[-3:] < "576")):
            stRead += str(self.ser.read(1))
	#print "QIOPEN: "+stRead

	print '### Intentando conectar a servidor Socket ###'
	if(stRead[-9:] == "OPEN: 0,0"):
	    print '###             Conexion exitosa          ###'
            self.parent.flRedOK = True
	else:
            if(stRead[-3:] == '562'):
                print '###   Conexion abierta de forma exitosa   ###'
                self.parent.flRedOK = True
            else:
                print '###     ERROR con el servidor Socket      ###'

        


    def inicializarTodo(self):
        print "cursor Datos Sistema"  
        c = self.conn.cursor()
        print "select Datos Sistema"  
        c.execute("SELECT idTransportista, idUnidad, idRutaActual, gprsProve, gprsUser, gprsPass, socketLiga, socketPuerto FROM configuraSistema")
        print "fetch Datos Sistema"  
        data = c.fetchone()
        if data is None:
            print 'No hay parametros de configuracon contacta al administrador'
        else:
            self.parent.idTransportista = data[0]
            self.parent.idUnidad = data[1]
            self.parent.ruta = data[2]
            self.provedor = data[3]
            self.usuarioProvedor = data[4]
            self.passProvedor = data[5]
            self.urlSocket = data[6]
            self.puertoSocket = data[7]
            self.parent.lblVelocidad.setText("")
            self.parent.lblMsg.setText("")

        c.close()
        c = None 

        connLn = sqlite3.connect('/home/pi/innobusmx/data/db/listaNegra')
        connLn.execute("DELETE FROM negra")
        connLn.commit()
        connLn.close()

        paso = 0
        print '#############################################'
        print '### Iniciando el modulo de comunicaciones ###'
        print '###                v0.02                  ###'
        print '#############################################'

#        cmd = "AT+QGPSEND\r"
#        self.ser.write(cmd.encode())
#        inigps = self.ser.read(64)
#        inigps = inigps.rstrip()
#        inigps = " ".join(inigps.split())
#        print(inigps)
        
	print '###           Reiniciando MODEM          ###'
	cmd = 'AT+QRST=1,0\r'
	self.ser.write(cmd.encode())
	stRead = ""
	while (stRead[-3:] != "RDY"):
            stRead += str(self.ser.read(1))
        #print "AT+QRST: " +stRead
              
        ini = ''
        
        self.inicializaGPS()
        
        self.inicializa3G()

        self.inicializaMSG()
        
        print '###   Sincronizando fecha con Servidor    ###'
        i = 0
#        while(i <= 3):
        while(i <= 1):
            i += 1
            print '###            Intento de Sync '+str(i)+'          ###'
            cmd = 'AT+QISEND=0\r'
            self.ser.write(cmd.encode())
            stRead = ""
            while (stRead[-5:] != "ERROR") and (stRead[-9:] != "SEND FAIL") and (stRead[-7:] != 'SEND OK') and (stRead[-1:] != ">"):
                stRead += str(self.ser.read(1))
            #print "QISEND (Hora): "+stRead

            if (stRead[-1:] == ">"):
                cmd = "00\r\x1A\r"
                self.ser.write(cmd.encode())
                stRead = ""
                i = 0
#               while (i < 1024) and (stRead[-8:] != '"recv",0') and (stRead[-5:] != "ERROR") and (stRead[-10:] != '"closed",0'):
                while (i < 100) and (stRead[-8:] != '"recv",0') and (stRead[-5:] != "ERROR") and (stRead[-10:] != '"closed",0'):
                    stRead += str(self.ser.read(1))
                    i += 1
                #print "send data: (" + str(i) + ")" + stRead
                    
                if (stRead[-8:] == '"recv",0') or (i == 100):
    		    cmd = 'AT+QIRD=0\r'
                    self.ser.write(cmd.encode())
                    stRead = ""
                    while (stRead[-2:] != 'OK') and (stRead[-5:] != 'ERROR'):
                        stRead += str(self.ser.read(1))
                    #print "QIRD: "+stRead
		    stRead = " ".join(stRead.split()) #se le aplica un split al mismo comando
                    #print "QIRDs: "+stRead


                    if (stRead[-2:] == 'OK'):
                        fecha = stRead.split(' ')
                        #print "Fecha: "
                        #print fecha
#                        print "ACTUALIZAR HORA "+fecha[3]+' '+fecha[4]
                        stRead = "\""+fecha[3]+' '+fecha[4]+"\""
                        print '###   Fecha '+stRead+'         ###'
                        comando = 'sudo date --set %s'%str(stRead)
                        os.system(comando)
                        i = 4
                        self.parent.flRed = True
                        #print "Connect bitacora de inicio"  
                        #conn = sqlite3.connect(cdDb)
                        #c = con.cursor()
                        self.conn.execute("INSERT INTO inicio (fecha) values (?)",(stRead,))
                        #c.execute("UPDATE tgps SET enviado = 1 WHERE idPos = ?", (idActualizar,))
                        self.conn.commit()
                        #c.close()
                        #conn.close()
                        #conn = None


                        

        print '#############################################'




              

        
      
    def mostrarHora(self):
        print "Obtener coordenada GPS"
        self.parent.modem.obtenerCoordenadaGPS()
        self.parent.lblHora.setText(time.strftime("%d/")+self.mes[int(time.strftime("%m"))]+time.strftime("/%Y %H:%M:%S"))
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

        QtCore.QTimer.singleShot(1000, self.mostrarHora)


class inicioGPS(QtCore.QThread):
    
#    def __init__(self, parent, obj, flGPS, noGPS):
    def __init__(self, parent, ser, flGPS, noGPS, connT, conn):
        qtcore.QThread.__init__(self)
        self.parent = parent
        self.noGPS = noGPS
        self.ser = ser
        self.connT = connT
        self.conn = conn
        #self.connT = sqlite3.connect('/home/pi/innobusmx/data/db/gps')
        #self.conn = sqlite3.connect('/home/pi/innobusmx/data/db/aforo')

    def run(self):
        accion = 1
        #while (True):
            #self.parent.obj.realizarAccion(accion)
            #accion = (accion % 10) + 1

    def obtenerCoordenadaGPS(self):
        '''
            ##############################################################
                Modulo que obteniene la coordenada GPS la guarda cuando
                el GPS se establece de manera correcta.
            ##############################################################
        '''
        #self.parent.noGPS.setPixmap(QtGui.QPixmap(""))
        #self.parent.lblMsg.setText("o")
        cmd = 'AT+QGPSLOC=0\r' 
        self.ser.write(cmd.encode())
        stRead = ""
        while (stRead[-2:] != "OK") and not ((stRead[-10:] >= "ERROR: 501") and (stRead[-10:] <= "ERROR: 549")):
            stRead += str(self.ser.read(1))
        print "QGPSLOC: "+stRead
        #self.parent.lblMsg1.setText("QGPSLOC: "+stRead)
        #time.sleep(2)
        self.parent.flGPS = (stRead[-2:] == "OK")
        if(stRead[-2:] == "OK"):
                self.parent.flGPS = True
#            try:
#                self.noGPS.setPixmap(QtGui.QPixmap(""))
		stRead = " ".join(stRead.split()) #se le aplica un split al mismo comando
		my_list = stRead.split(",")
                # 0 Hora  (hh-mm-ss)
		# 1 latitud
		# 2 longitud
                # 7 velocidad
                # 9 Fecha (dd-mm-aa)
                # print my_list
		hora = my_list[0][23:25] + ":" + my_list[0][25:27] + ":" + my_list[0][27:29]
		latitud = my_list[1][0:-1]
		if (my_list[1][-1:] == 'S'):
                    latitud = '-' + latitud
		longitud = my_list[2][0:-1]
		velGPS = my_list[7]
		fecha = my_list[9][0:2] + "-" + my_list[9][2:4] + "-20" + my_list[9][4:6]
                idInser = my_list[9][4:6]+my_list[0][23:29]
                l = float(latitud[0:2]) + (float(latitud[2:])/60)
                latitud = ("%.6f" % l)
                l = float(longitud[0:3]) + (float(longitud[3:])/60)
                longitud = ("%.6f" % l)
		if (my_list[2][-1:] == 'W'):
                    longitud = '-' + longitud
                print '###         Dato valido insertandolo      ###'
                #print "Connect insertando dato GPS"  
                #connT = sqlite3.connect(cdDbT)
                #c = conn.cursor()
                self.parent.idCons += 1
                print "Insert GPS"
                #self.parent.stSQLGPS = 'insert into tgps (hora, latitud, longitud, fecha, velocidad,idPos,enviado, idCons) values ('+hora+','+latitud+','+longitud+','+fecha+','+velGPS+',' +idInser+', 0,'+self.parent.idCons+')'
                self.connT.execute('insert into tgps (hora, latitud, longitud, fecha, velocidad,idPos,enviado, idCons) values (?, ?, ?, ?, ?, ?, 0, ?)', (hora, latitud, longitud, fecha, velGPS, idInser, self.parent.idCons))
                print "commit insertando dato GPS"  
                self.connT.commit()
                self.parent.lblVelocidad.setText(str(velGPS))
                datetimes = fecha + ' ' + hora
                gpr = '1,'+str(self.parent.idTransportista)+','+str(self.parent.idUnidad)+','+str(datetimes)+','+str(latitud)+','+str(longitud)+','+str(velGPS)+','+str(self.parent.idCons)+'\r'+''
                print "GPS (envio) " + gpr
                self.parent.procesoDeEnvio(gpr, idInser, 1, 0)

                
 #           except:
 #                print '###   GPS fallo el parseo del dato   ###'
        else:
            velGPS = 0
            self.parent.lblVelocidad.setText("-")
            self.parent.flGPS = False







def main():
    app = QtGui.QApplication(sys.argv)
    ex = mainWin()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
