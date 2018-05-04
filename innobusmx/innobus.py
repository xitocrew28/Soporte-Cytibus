#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtGui
from PyQt4 import QtCore
#import serial
import sqlite3
import os
#from time import strftime
import time
#import threading
#mport subprocess
#import datetime
#import urllib
#from PyQt4 import QtCore as qtcore
#from curses import ascii
#import base64
#import re
#from func import funciones


#retardo = 1
#intervaloTiempoParaInFin = 5
#nVuelta = 0



from ClReloj import clReloj
from ClSerial import clSerial
from ClModem import clQuectel
from ClDB import sqLite
from ClMifare import clMifare


class mainWin(QtGui.QMainWindow):

    stVersion = "v1.28"
    flRFID = False
    
    def __init__(self):
        super(mainWin, self).__init__()

        '''
            ############################################################
                    Pantalla Principal del Sistema de Prepago

            ############################################################
        '''
        if os.path.exists('/home/pi/innobusmx/innobus.log'):
            os.remove('/home/pi/innobusmx/innobus.log')
        self.logo = QtGui.QLabel(self)
        self.logo.setScaledContents(True)
        pathImgFondo = os.path.join('/home/pi/innobusmx/data/img/wall2.jpg')
        self.logo.setPixmap(QtGui.QPixmap(pathImgFondo))
        self.logo.move(0, 0)
        self.logo.resize(800, 480)
        
        self.lblOperador = QtGui.QLabel(self)
        self.lblOperador.setScaledContents(True)
        self.lblOperador.move(90, 5)
        self.lblOperador.resize(280, 368)

        self.lblVersion = QtGui.QLabel('', self)
        self.lblVersion.resize(self.width(), 50)
        self.lblVersion.move(750, 42)
        self.lblVersion.setStyleSheet('QLabel { font-size: 8pt; font-family: Arial; color:Gray}')
        self.lblVersion.setText(self.stVersion)

        self.lblNS = QtGui.QLabel('', self)
        self.lblNS.resize(self.width(), 50)
        self.lblNS.move(5, 435)
        self.lblNS.setStyleSheet('QLabel { font-size: 8pt; font-family: Arial; color:White}')

        self.lblNSFirmware = QtGui.QLabel('', self)
        self.lblNSFirmware.resize(self.width(), 50)
        self.lblNSFirmware.move(5, 450)
        self.lblNSFirmware.setStyleSheet('QLabel { font-size: 8pt; font-family: Arial; color:White}')


        self.lblUnidad = QtGui.QLabel('', self)
        self.lblUnidad.resize(self.width(), 50)
        self.lblUnidad.move(650, 120)
        self.lblUnidad.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:White}')

        self.lblNombreOperador = QtGui.QLabel('', self)
        self.lblNombreOperador.resize(self.width(), 50)
        self.lblNombreOperador.move(65, 380)
        self.lblNombreOperador.setStyleSheet('QLabel { font-size: 20pt; font-family: Arial; color:White}')

        self.lblRuta = QtGui.QLabel('', self)
        self.lblRuta.resize(self.width(), 50)
        self.lblRuta.move(620, 260)
        self.lblRuta.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:White}')

        self.lblVuelta = QtGui.QLabel('', self)
        self.lblVuelta.resize(self.width(), 50)
        self.lblVuelta.move(650, 190)
        self.lblVuelta.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:White}')

        self.lblVelocidad = QtGui.QLabel('', self)
        self.lblVelocidad.resize(self.width(), 50)
        self.lblVelocidad.move(670, 325)
        self.lblVelocidad.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:White}')

        self.lblHora = QtGui.QLabel('', self)
        self.lblHora.resize(self.width(), 50)
        self.lblHora.move(550, 440)
        self.lblHora.setStyleSheet('QLabel { font-size: 14pt; font-family: Arial; color:White}')

        self.lblMsg = QtGui.QLabel('', self)
        self.lblMsg.resize(self.width(), 50)
        self.lblMsg.move(10, 380)
        self.lblMsg.setStyleSheet('QLabel { font-size: 8pt; font-family: Arial; color:Blue}')

        self.lblMsg1 = QtGui.QLabel('', self)
        self.lblMsg1.resize(self.width(), 50)
        self.lblMsg1.move(10, 340)
        self.lblMsg1.setStyleSheet('QLabel { font-size: 8pt; font-family: Arial; color:Blue}')

        self.msg = QtGui.QLabel('', self)
        self.msg.resize(self.width(), 50)
        self.msg.move(135, 400)
        self.msg.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:red}')

        '''
            ############################################################
                Aqui estan las variables que necesito para mostrar
                        la informacion de los aforo
            ############################################################
        '''

        self.lblAlteTurno = QtGui.QLabel('', self)
        self.lblAlteTurno.resize(self.width(), 50)
        self.lblAlteTurno.move(200, 360)
        self.lblAlteTurno.setStyleSheet('QLabel { font-size: 25pt; font-family: Arial; color:white}')


        self.lblAlteTurnoDos = QtGui.QLabel('', self)
        self.lblAlteTurnoDos.resize(self.width(), 50)
        self.lblAlteTurnoDos.move(200, 400)
        self.lblAlteTurnoDos.setStyleSheet('QLabel { font-size: 25pt; font-family: Arial; color:white}')

        imgTarjetaAtras = "/home/pi/innobusmx/data/img/imgTarjetas/Cl.jpg"
        imgUsuarioTarjeta = "/home/pi/innobusmx/data/user/admin.Jpeg"

        self.no3G = QtGui.QLabel(self)
        self.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/no3G.Jpeg"))
        self.no3G.setScaledContents(True)
        self.no3G.move(770,425)
        self.no3G.resize(20, 20)

        self.noGPS = QtGui.QLabel(self)
        self.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noGPSEncendido.png"))
        self.noGPS.setScaledContents(True)
        self.noGPS.move(740,425)
        self.noGPS.resize(20, 20)

        self.noSocket = QtGui.QLabel(self)
        self.noSocket.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noSocket.png"))
        self.noSocket.setScaledContents(True)
        self.noSocket.move(710,425)
        self.noSocket.resize(20, 20)

        self.noFTP = QtGui.QLabel(self)
        self.noFTP.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noFTP.Jpeg"))
        self.noFTP.setScaledContents(True)
        self.noFTP.move(680,425)
        self.noFTP.resize(20, 20)

        self.noRDIF = QtGui.QLabel(self)
        self.noRDIF.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noRFID.Jpeg"))
        self.noRDIF.setScaledContents(True)
        self.noRDIF.move(650,425)
        self.noRDIF.resize(20, 20)

        self.noRed = QtGui.QLabel(self)
        self.noRed.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noRed.Jpeg"))
        self.noRed.setScaledContents(True)
        self.noRed.move(620,425)
        self.noRed.resize(20, 20)

        self.noSIM = QtGui.QLabel(self)
        self.noSIM.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noSIM.png"))
        self.noSIM.setScaledContents(True)
        self.noSIM.move(550,425)
        self.noSIM.resize(32, 20)

        
        self.flFecha = False
        self.flFTP = False
        self.flRed = False
        self.flSocket = False
        self.flComm = True
        self.iComm = 0
        self.flRFID = False
        self.flSIM = False
        self.iccid = ""

        self.flGPS = False
        self.flGPSOK = False

        self.serialNumber = ""
        self.version = ""
        self.TISC = ""
        self.stImgTarjeta = ""
        self.stSaldo = ""
        self.stTarjeta = ""
        self.stNombre = ""
        self.stApellido = ""
        self.stSaldoInsuficiente = ""
        self.stMsg = ""

        self.imgTarjeta = QtGui.QLabel(self)
        self.imgTarjeta.setPixmap(QtGui.QPixmap(""))
        #self.imgTarjeta.setPixmap(QtGui.QPixmap(imgTarjetaAtras))
        self.imgTarjeta.setScaledContents(True)
        self.imgTarjeta.move(0,0)
        self.imgTarjeta.resize(800, 480)

        self.imgDefault = QtGui.QLabel(self)
        self.imgDefault.setPixmap(QtGui.QPixmap(""))
        self.imgDefault.setScaledContents(True)
        self.imgDefault.move(5,5)
        self.imgDefault.resize(422,470)
        #antigui tamano
        #self.imgDefault.resize(335,345)

        #self.lblNombreT = QtGui.QLabel('', self)
        #self.lblNombreT.resize(self.width(), 50)
        #self.lblNombreT.move(435, 100)
        #self.lblNombreT.setStyleSheet('QLabel { font-size: 15pt; font-family: Arial; color:White}')
        #self.lblNombreT.setText("NOMBRE")
        #self.lblNombreT.hide()

        self.lblNombre = QtGui.QLabel('', self)
        self.lblNombre.resize(376, 70)
        self.lblNombre.move(424, 85)
        self.lblNombre.setStyleSheet('QLabel { font-size: 40pt; font-family: Arial; color:White}')
        self.lblNombre.setAlignment(QtCore.Qt.AlignCenter)
        

        #self.lblApellidoT = QtGui.QLabel('', self)
        #self.lblApellidoT.resize(self.width(), 50)
        #self.lblApellidoT.move(435, 200)
        #self.lblApellidoT.setStyleSheet('QLabel { font-size: 15pt; font-family: Arial; color:White}')
        #self.lblApellidoT.setText("APELLIDO")
        #self.lblApellidoT.hide()

        self.lblApellido = QtGui.QLabel('', self)
        self.lblApellido.resize(376, 50)
        self.lblApellido.move(424, 150)
        self.lblApellido.setStyleSheet('QLabel { font-size: 25pt; font-family: Arial; color:White}')
        self.lblApellido.setAlignment(QtCore.Qt.AlignCenter)

        #self.lblSaldoT = QtGui.QLabel('', self)
        #self.lblSaldoT.resize(self.width(), 50)
        #self.lblSaldoT.move(435, 300)
        #self.lblSaldoT.setStyleSheet('QLabel { font-size: 15pt; font-family: Arial; color:White}')
        #self.lblSaldoT.setText("SALDO")
        #self.lblSaldoT.hide()

        self.lblSaldo = QtGui.QLabel('', self)
        self.lblSaldo.resize(376, 75)
        self.lblSaldo.move(424, 300)
        self.lblSaldo.setStyleSheet('QLabel { font-size: 50pt; font-family: Arial; color:White}')
        self.lblSaldo.setAlignment(QtCore.Qt.AlignCenter)

        self.lblMsg = QtGui.QLabel('', self)
        self.lblMsg.resize(self.width(), 75)
        self.lblMsg.move(750, 385)
        self.lblMsg.setStyleSheet('QLabel { font-size: 8pt; font-family: Arial; color:Red}')

        self.lblSaldoInsuficiente = QtGui.QLabel('', self)
        self.lblSaldoInsuficiente.resize(self.width(), 75)
        self.lblSaldoInsuficiente.move(470, 410)
        self.lblSaldoInsuficiente.setStyleSheet('QLabel { font-size: 35pt; font-family: Arial; color:Red}')

        self.lblSS = QtGui.QLabel('', self)
        self.lblSS.resize(self.width(), 50)
        self.lblSS.move(270, 45)
        self.lblSS.setStyleSheet('QLabel { font-size: 45pt; font-family: Arial; color:White}')

        self.lblVAI = QtGui.QLabel('', self)
        self.lblVAI.resize(self.width(), 50)
        self.lblVAI.move(150, 45)
        self.lblVAI.setStyleSheet('QLabel { font-size: 50pt; font-family: Arial; color:White}')

        self.lblSSMsg = QtGui.QLabel('', self)
        self.lblSSMsg.resize(self.width(), 50)
        self.lblSSMsg.move(150, 350)
        self.lblSSMsg.setStyleSheet('QLabel { font-size: 45pt; font-family: Arial; color:White}')

        self.lblTarjetas = QtGui.QLabel('', self)
        self.lblTarjetas.resize(self.width(), 50)
        self.lblTarjetas.move(180, 220)
        self.lblTarjetas.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:Yellow}')

        self.lblNV = QtGui.QLabel('', self)
        self.lblNV.resize(self.width(), 50)
        self.lblNV.move(265, 45)
        self.lblNV.setStyleSheet('QLabel { font-size: 45pt; font-family: Arial; color:White}')

        self.lblInFinVuelta = QtGui.QLabel('', self)
        self.lblInFinVuelta.resize(self.width(), 50)
        self.lblInFinVuelta.move(200, 220)
        self.lblInFinVuelta.setStyleSheet('QLabel { font-size: 40pt; font-family: Arial; color:red}')

        self.setGeometry(-1, 0, 800, 480)
        self.setWindowTitle('CytiBus '+self.stVersion)
        self.setStyleSheet('''QMainWindow { background-color:#1D2556;}
            QLabel{font-size: 15pt; font-family: Courier; color:black;
            font-weight: bold}''')

        conn = sqlite3.connect('/home/pi/innobusmx/data/db/aforo')
        c = conn.cursor()
        #conn.execute('UPDATE parametros SET urlAPN="innobusmx.itelcel.com", userAPN="", pwdAPN="", urlSocket="192.168.2.175", puertoSocket=5800, urlFTP="192.168.2.175", puertoFTP=21')
        conn.execute('UPDATE parametros SET urlAPN="internet.itelcel.com", userAPN="webgprs", pwdAPN="webgprs2002", urlSocket="innovaslp.dyndns.org", puertoSocket=11004, urlFTP="innovaslp.dyndns.org", puertoFTP=21')
        conn.commit()
        c.execute("SELECT economico FROM parametros")
        data = c.fetchone()
        if data is None:
            self.lblUnidad.setText("")
        else:
            self.lblUnidad.setText(str(data[0]))
        c.execute('select fechaHora, ruta.nombre, csn, num_vuelta, tTurno.nombre, inicioFin from soloVuelta, ruta, tTurno WHERE soloVuelta.idRuta = ruta.Id AND soloVuelta.turno = tTurno.idTurno ORDER BY idSoloVuelta DESC LIMIT 1')
        data = c.fetchone()
        c.close()
        if (data is None) or (data[5] == "F"):
            self.lblOperador.setPixmap(QtGui.QPixmap(""))
            self.lblRuta.setText("")
            self.lblVuelta.setText("")
        else:
            self.lblRuta.setText(data[1])
            imgChofer = "data/user/%s.Jpeg"%data[2]
            scriptChofer = os.path.join(self.dir, imgChofer)
            self.lblOperador.setPixmap(QtGui.QPixmap(scriptChofer))
            self.lblVuelta.setText(str(data[3]))
        conn.close

        #self.imgDefault.setPixmap(QtGui.QPixmap('/home/pi/innobusmx/data/user/04203/04203532545780.Jpeg'))
        #self.imgTarjeta.setPixmap(QtGui.QPixmap('/home/pi/innobusmx/data/img/imgTarjetas/NO.jpg'))
        #self.lblNombre.setText("Alfredo")
        #self.lblApellido.setText("Blanco Perez")
        #self.lblSaldo.setText("$100.00")               


        #self.lblOperador.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/user/Shapes050.jpeg"))
        #thread = loadImageThread(file="/home/pi/innobusmx/data/img/noGPSEncendido.png", w=512, h=512)
        #self.connect(thread, QtCore.SIGNAL("showImage(QString)"), self.showImage)
        #thread.start()
        
        #thread = clReloj(self)
        #self.connect(thread, QtCore.SIGNAL("showImage(QString)"), self.showImage)
        #thread.start()

        #self.showMaximized()
        #self.setWindowFlags(QtCore.Qt.CustomizeWindowHint)
        #self.showFullScreen()
        self.center()
        self.show()

        clreloj = clReloj(self)
        clreloj.start()        
      
    def center(self): 
        frameGm = self.frameGeometry()
        centerPoint = QtGui.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())        

class Screen():
    
    def __init__(self, parent):
        self.parent = parent
        self.flG = False
        self.red = False
        self.ftp = False
        self.flR = True
        self.rfid = not self.parent.flRFID
        self.icomm = -999
        self.sim = False
        self.tisc = ""
        self.socket = False
        self.show()

    def show(self):

        #clmodem.obtenerMensaje()
        #print "iComm:",self.parent.iComm
        if (self.icomm != self.parent.iComm):
            if (self.parent.iComm == 0 or self.parent.iComm == 99):
                self.parent.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/no3G.Jpeg"))
            elif (self.parent.iComm == 1):
                self.parent.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/no3G.png"))
            elif (self.parent.iComm >= 2 and self.parent.iComm <= 10):
                self.parent.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/3G25.png"))
            elif (self.parent.iComm >= 11 and self.parent.iComm <= 20):
                self.parent.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/3G50.png"))
            elif (self.parent.iComm >= 21 and self.parent.iComm <= 30):
                self.parent.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/3G75.png"))
            elif (self.parent.iComm >= 31 and self.parent.iComm <= 98):
                self.parent.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/3G.png"))
            self.icomm = self.parent.iComm

        if (self.parent.flRFID != self.rfid):
            if (not self.parent.flRFID):
                self.parent.noRDIF.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noRFID.Jpeg"))
            else:
                self.parent.noRDIF.setPixmap(QtGui.QPixmap(""))
            self.rfid = self.parent.flRFID

        if (self.parent.flSocket != self.socket):
            if (not self.parent.flSocket):
                self.parent.noSocket.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noSocket.png"))
            else:
                self.parent.noSocket.setPixmap(QtGui.QPixmap(""))
            self.socket = self.parent.flSocket

        if (self.parent.flRed != self.red):
            if (not self.parent.flRed):
                self.parent.noRed.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noRed.Jpeg"))
            else:
                self.parent.noRed.setPixmap(QtGui.QPixmap(""))
            self.red = self.parent.flRed




        if (self.parent.TISC != self.tisc):
            if (self.parent.TISC != ""):
                #print "Saldo Insuficiente",self.parent.stSaldoInsuficiente
                #print "Nombre",self.parent.stNombre, self.parent.stApellido
                self.parent.imgDefault.setPixmap(QtGui.QPixmap(self.parent.TISC))
                self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(self.parent.stImgTarjeta))
                self.parent.lblNombre.setText(self.parent.stNombre)
                self.parent.lblApellido.setText(self.parent.stApellido)
                self.parent.lblSaldo.setText(self.parent.stSaldo)               
                self.parent.lblSaldoInsuficiente.setText(self.parent.stSaldoInsuficiente)
                self.parent.lblMsg.setText(self.parent.stMsg)
                #if (self.parent.stSaldo != ""):
                #    self.parent.lblSaldoT.show()
                #if (self.parent.stNombre != ""):
                #    self.parent.lblNombreT.show()
                #    self.parent.lblApellidoT.show()                    
            else:
                self.parent.imgDefault.setPixmap(QtGui.QPixmap(""))
                self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(""))
                self.parent.lblNombre.setText("")
                self.parent.lblApellido.setText("")
                self.parent.lblSaldo.setText("")
                self.parent.lblSaldoInsuficiente.setText("")
                self.parent.lblMsg.setText("")
                #self.parent.lblNombreT.hide()
                #self.parent.lblApellidoT.hide()
                #self.parent.lblSaldoT.hide()
            self.tisc = self.parent.TISC


        if (self.parent.flSIM != self.sim):
            if (not self.parent.flSIM):
                self.parent.noSIM.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noSIM.png"))
            else:
                self.parent.noSIM.setPixmap(QtGui.QPixmap(""))
            self.sim = self.parent.flSIM

        if (not self.parent.flGPSOK):
            self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noGPSEncendido.png"))
        else:
            if (self.flG):
                if (self.parent.flGPS):
                    self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/GPS.png"))
                else:
                    self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noGPS.png"))
                self.flG = False
            else:
                self.parent.noGPS.setPixmap(QtGui.QPixmap(""))
                self.flG = True
        '''
        if (self.parent.flFTP != self.ftp):
            if (self.parent.flFTP):
                if (self.flftp):
                    self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noGPS.png"))
                    self.flG = False
                else:
                    self.parent.noFTP.setPixmap(QtGui.QPixmap(""))
                    self.flG = True
            else:
                self.parent.noFTP.setPixmap(QtGui.QPixmap(""))
            self.ftp = self.parent.flFTP
        '''     
            

        QtCore.QTimer.singleShot(250, self.show)



def main():
    app = QtGui.QApplication(sys.argv)
    ex = mainWin()
    #ex.start()
    #self.modem = inicioGPS(self, self.ser, self.flGPS, self.noGPS)
    #self.tresg = TresG(self, self.ser, self.modem)
    #self.funcCore = funciones(self)
    #self.funcCore.datosVuelta        
    cldb = sqLite()




    #clStatus = Status(ex)
    #clStatus.start()

    clserial = clSerial(ex, cldb)
#    serial.daemon = True
#    clserial.start()

    clmodem = clQuectel(ex, cldb, clserial)
    clmodem.start()


    clmifare = clMifare(ex, cldb, clserial, clmodem)
    clmifare.start()

    clscreen = Screen(ex)
    #clscreen.start()

    sys.exit(app.exec_())    


if __name__ == '__main__':
    main()
