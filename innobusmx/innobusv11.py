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

    stVersion = "v1.1"
    
    def __init__(self):
        super(mainWin, self).__init__()

        '''
            ############################################################
                    Pantalla Principal del Sistema de Prepago

            ############################################################
        '''


        self.logo = QtGui.QLabel(self)
        self.logo.setScaledContents(True)
        pathImgFondo = os.path.join('/home/pi/innobusmx/data/img/wall2.jpg')
        self.logo.setPixmap(QtGui.QPixmap(pathImgFondo))
        self.logo.move(0, 0)
        self.logo.resize(800, 480)
        
        self.lblOperador = QtGui.QLabel(self)
        self.lblOperador.setScaledContents(True)
        self.lblOperador.move(30, 120)
        self.lblOperador.resize(243, 320)

        self.lblVersion = QtGui.QLabel('', self)
        self.lblVersion.resize(self.width(), 50)
        self.lblVersion.move(5, 435)
        self.lblVersion.setStyleSheet('QLabel { font-size: 10pt; font-family: Arial; color:White}')
        self.lblVersion.setText("CytiBus "+self.stVersion)

        self.lblNS = QtGui.QLabel('', self)
        self.lblNS.resize(self.width(), 50)
        self.lblNS.move(5, 455)
        self.lblNS.setStyleSheet('QLabel { font-size: 8pt; font-family: Arial; color:White}')
        #self.lblNS.setText("NS: Ix01170017")

        self.lblNSFirmware = QtGui.QLabel('', self)
        self.lblNSFirmware.resize(self.width(), 50)
        self.lblNSFirmware.move(750, 398)
        self.lblNSFirmware.setStyleSheet('QLabel { font-size: 8pt; font-family: Arial; color:White}')
        #self.lblNSFirmware.setText("Vx0.08")


        self.lblUnidad = QtGui.QLabel('', self)
        self.lblUnidad.resize(self.width(), 50)
        self.lblUnidad.move(650, 120)
        self.lblUnidad.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:White}')
        #self.lblUnidad.setText("5300")

        self.lblNombreOperador = QtGui.QLabel('', self)
        self.lblNombreOperador.resize(self.width(), 50)
        self.lblNombreOperador.move(65, 380)
        self.lblNombreOperador.setStyleSheet('QLabel { font-size: 20pt; font-family: Arial; color:White}')
        #self.lblNombreOperador.setText("ALFREDO BLANCO PEREZ")

        self.lblRuta = QtGui.QLabel('', self)
        self.lblRuta.resize(self.width(), 50)
        self.lblRuta.move(620, 260)
        self.lblRuta.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:White}')
        #self.lblRuta.setText("28")

        self.lblVuelta = QtGui.QLabel('', self)
        self.lblVuelta.resize(self.width(), 50)
        self.lblVuelta.move(650, 190)
        self.lblVuelta.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:White}')
        #self.lblVuelta.setText("01")

        self.lblVelocidad = QtGui.QLabel('', self)
        self.lblVelocidad.resize(self.width(), 50)
        self.lblVelocidad.move(670, 325)
        self.lblVelocidad.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:White}')
        #self.lblVelocidad.setText("50")

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

        self.imgTarjeta = QtGui.QImage(800,480, QtGui.QImage.Format_ARGB32)
        self.imgTarjeta.loadFromData (imgTarjetaAtras)
        #self.imgTarjeta.setScaledContents(True)
        #self.imgTarjeta.move(0,0)
        #self.imgTarjeta.resize(800, 480)
        
        '''
        self.imgTarjeta = QtGui.QLabel(self)
        self.imgTarjeta.setPixmap(QtGui.QPixmap(""))
        #self.imgTarjeta.setPixmap(QtGui.QPixmap(imgTarjetaAtras))
        self.imgTarjeta.setScaledContents(True)
        self.imgTarjeta.move(0,0)
        self.imgTarjeta.resize(800, 480)
        '''
    


        self.noRed = QtGui.QLabel(self)
        self.noRed.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noRed.Jpeg"))
        self.noRed.setScaledContents(True)
        self.noRed.move(770,425)
        self.noRed.resize(20, 20)

        self.flFecha = False
        self.flRed = False
        self.flRedOK = False
        self.flComm = True
        self.iComm = 0

        self.noGPS = QtGui.QLabel(self)
        self.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noGPSEncendido.png"))
        self.noGPS.setScaledContents(True)
        self.noGPS.move(740,425)
        self.noGPS.resize(20, 20)

        self.flGPS = False
        self.flGPSOK = False

        self.noRDIF = QtGui.QLabel(self)
        self.noRDIF.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noRFID.Jpeg"))
        self.noRDIF.setScaledContents(True)
        self.noRDIF.move(710,425)
        self.noRDIF.resize(20, 20)

        self.noSevidor = QtGui.QLabel(self)
        self.noSevidor.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noServidor.Jpeg"))
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
        self.lblNombreApe.setStyleSheet('QLabel { font-size: 50pt; font-family: Arial; color:White}')

        self.lblSaldo = QtGui.QLabel('', self)
        self.lblSaldo.resize(self.width(), 75)
        #antiguo
        #self.lblSaldo.move(480, 260)

        self.lblSaldo.move(40, 300)
        #self.lblSaldo.setText("$155.55")
       
        #self.lblSaldo.move(400, 300)
        self.lblSaldo.setStyleSheet('QLabel { font-size: 55pt; font-family: Arial; color:White}')
            #E6F9AF
        #self.lblNombreApe.hide()

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


        conn = sqlite3.connect('/home/pi/innobusmx/data/db/tarifas')
        conn.execute("UPDATE tar SET cantidad=415 where nom='01'")
        conn.execute("UPDATE tar SET cantidad=830 where nom='02'")
        conn.execute("UPDATE tar SET cantidad=900 where nom='03'")
        conn.execute("UPDATE tar SET cantidad=415 where nom='04'")
        conn.commit()
        conn.close

        conn = sqlite3.connect('/home/pi/innobusmx/data/db/aforo')
        c = conn.cursor()
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


        thread = loadImageThread(file="/home/pi/innobusmx/data/img/noGPSEncendido.png", w=512, h=512)
        self.connect(thread, QtCore.SIGNAL("showImage(QString, int, int)"), self.showImage)
        thread.start()
        
        
       
        #self.showMaximized()
        #self.setWindowFlags(QtCore.Qt.CustomizeWindowHint)
        #self.showFullScreen()
        self.center()
        self.show()

    def showImage(self, filename, w, h):
        pixmap = QtGui.QPixmap(filename).scaled(w,h)
        self.image.setPixmap(pixmap)
        self.image.repaint()
        
    def center(self): 
        frameGm = self.frameGeometry()
        centerPoint = QtGui.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def muestraCredencial(self, imgT, imgU, stNombre, saldo):
        self.imgTarjeta.loadFromData (imgT)
        #self.imgTarjeta.setPixmap(QtGui.QPixmap(imgT))
        self.imgDefault.setPixmap(QtGui.QPixmap(imgU))
        self.lblNombreApe.setText(stNombre)
        self.lblSaldo.setText(str(saldo))

class loadImageThread(QtCore.QThread):
    def __init__(self, file, w, h):
        QtCore.QThread.__init__(self)
        self.file = file;
        self.w = w
        self.h = h

    def __del__(self):
        self.wait()

    def run(self):
        self.emit(QtCore.SIGNAL('showImage(QString. int, int)'),self.file, self.w, self.h)
        

class Status():
    def __init__(self, parent):
        self.parent = parent
        self.show()

    def show(self):
        #print "showStatus"
        if (self.parent.iComm > 5 and self.parent.iComm != 99):
            if (self.parent.iComm < 20):
                self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/3G.png"))
            else:
                self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/i3G.png"))                
        else:
            self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/no3G.png"))
            
        if (not self.parent.flGPSOK):
            self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noGPSEncendido.png"))
        else:
            if (self.parent.flGPS):
                self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/GPS.png"))
                #print "'GPS'"
            else:
                self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noGPS.png"))
                #print "'NoGPS'"
        QtCore.QTimer.singleShot(1000, self.show)







def main():
    app = QtGui.QApplication(sys.argv)
    ex = mainWin()
    #ex.start()
    #self.modem = inicioGPS(self, self.ser, self.flGPS, self.noGPS)
    #self.tresg = TresG(self, self.ser, self.modem)
    #self.funcCore = funciones(self)
    #self.funcCore.datosVuelta        
    cldb = sqLite()

    clreloj = clReloj(ex, ex.noGPS)
    clreloj.start()


    clStatus = Status(ex)
    #clStatus.start()

    clserial = clSerial(ex, cldb)
#    serial.daemon = True
#    clserial.start()

    clmodem = clQuectel(ex, cldb, clserial.sPort3G, clserial.velocidad)
    clmodem.start()


    clmifare = clMifare(ex, cldb, clserial, clmodem)
    clmifare.start()

    sys.exit(app.exec_())    


if __name__ == '__main__':
    main()
