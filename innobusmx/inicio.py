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
#sys.path.insert(0, '/home/hiram/Documentos/innobusmx/src/')
sys.path.insert(0, '/home/pi/innobusmx/src/')
from func import funciones
#from func import reloj
#from func import fecha
from rwdux3G import rwsGPS


class reloj():
    def __init__(self, parent):
        self.parent = parent
        self.mes=["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        self.mostrarHora()
        
    def mostrarHora(self):
        self.parent.lblHora.setText(time.strftime("%d/")+self.mes[int(time.strftime("%m"))]+time.strftime("/%Y %H:%M:%S"))
        if (self.parent.flGPS):
            self.parent.noGPS.setPixmap(QtGui.QPixmap(""))
        else:
            self.parent.noGPS.setPixmap(QtGui.QPixmap("data/img/noGPS.Jpeg"))
            
            
        QtCore.QTimer.singleShot(1000, self.mostrarHora)

       


class mainWin(QtGui.QMainWindow):
    def __init__(self):
        super(mainWin, self).__init__()
        self.dir = os.path.dirname(__file__)
        self.cdDb = os.path.join(self.dir, 'data/db/tarifas')
        self.openDBAforo = os.path.join(self.dir,'data/db/aforo')
        self.openDBFotos = os.path.join(self.dir,'data/db/existeFoto')
        self.openDBEV2 = os.path.join(self.dir,'data/db/ev2')
        #Definicion de variables globales
        self.retardo = 1
        self.intervaloTiempoParaInFin = 5
        self.nVuelta = 0

#        self.sPort = '/dev/ttyUSB1'
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
        self.initUI()

        csnS = "HOLA"
        self.funcCore = funciones(self, csnS)
        #self.funcCore.dormir()

        self.hora = reloj(self)

        self.funcCore.datosVuelta
#        self.usbRFID = usbRFID(self)
        
        '''
        self.esS = escucharSerial(self, self.funcCore)
        self.esS.daemon = True
        self.connect(self.esS, self.esS.signal, self.funcCore.mostrarFoto)
        self.connect(self.esS, self.esS.signal2, self.funcCore.borrarFoto)
        self.esS.start()
        
        self.obj = rwsGPS(self)
        self.modem = inicioGPS(self, self.obj, self.flGPS, self.noGPS)
        self.modem.daemon = True
        self.modem.start()
        '''
        


    def initSerial(self):
        print '*****************************************Iniciando puerto serie'
        #self.sPort = '/dev/ttyUSB0'
        #velocidad = 115200
        self.ser = serial.Serial(self.sPort, self.velocidad)
        self.ser.flushInput()
        self.ser.flushOutput()
        return self.ser

    def initSerialEsperandoOK(self):
        print '*******************************Iniciando puerto esperando el OK'
        #self.sPort = '/dev/ttyUSB0'
        #velocidad = 115200
        self.ser = serial.Serial(self.sPort, self.velocidad, timeout = 1)
        self.ser.flushInput()
        self.ser.flushOutput()
        return self.ser

    def closeSerial(self):
        print '****************************************Cerrando el puerto serie'
        self.ser.close()

    def initUI(self):
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


        conn = sqlite3.connect(self.openDBAforo)
        c = conn.cursor()
        c.execute("SELECT nunEco, Operador FROM configuraSistema")
        data = c.fetchone()
        if data is None:
            self.lblUnidad.setText("")
            self.lblNombreOperador.setText("")
        else:
            self.lblUnidad.setText(str(data[0]))
            self.lblNombreOperador.setText(data[1])
        c.close

        c = conn.cursor()
        c.execute('select fechaHora, ruta.nombre, csn, num_vuelta, tTurno.nombre, inicioFin from soloVuelta, ruta, tTurno WHERE soloVuelta.idRuta = ruta.Id AND soloVuelta.turno = tTurno.idTurno ORDER BY idSoloVuelta DESC LIMIT 1')
        data = c.fetchone()
        if data[5] == "F":
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
        c.close


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
        self.noRed.setPixmap(QtGui.QPixmap("data/img/noRed.Jpeg"))
        self.noRed.setScaledContents(True)
        self.noRed.move(770,425)
        self.noRed.resize(20, 20)

        self.noGPS = QtGui.QLabel(self)
        self.noGPS.setPixmap(QtGui.QPixmap("data/img/noGPS.Jpeg"))
        self.noGPS.setScaledContents(True)
        self.noGPS.move(740,425)
        self.noGPS.resize(20, 20)

        self.flGPS = False   

        self.noRDIF = QtGui.QLabel(self)
        if self.sPort == '':
            self.noRDIF.setPixmap(QtGui.QPixmap("data/img/noRFID.Jpeg"))
        else:
            self.noRDIF.setPixmap(QtGui.QPixmap(""))
        self.noRDIF.setScaledContents(True)
        self.noRDIF.move(710,425)
        self.noRDIF.resize(20, 20)

        self.noSevidor = QtGui.QLabel(self)
        self.noSevidor.setPixmap(QtGui.QPixmap("data/img/noServidor.Jpeg"))
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




def main():
    app = QtGui.QApplication(sys.argv)
    ex = mainWin()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
