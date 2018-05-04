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
import datetime
import urllib
from PyQt4 import QtCore as qtcore
from curses import ascii
import base64
import re
#sys.path.insert(0, '/home/pi/innobusmx/src/')
from func import funciones
#from rwdux3G import rwsGPS





class escucharSerial(qtcore.QThread):
    #el constructor no hace falta especificarlo
    #ya que la clase lo hace por nosotros.
    def __init__(self, parent, funcCore):
           #threading.Thread.__init__(self)
           qtcore.QThread.__init__(self)
           self.parent = parent
           self.funcCore = funcCore
           self.signal = qtcore.SIGNAL("signal")
           self.signal2 = qtcore.SIGNAL("signal2")
           #self.funcCore.dormir()
           print '     Escuchar Serial'


    def run(self):
        self.preaderLocal = self.parent.initSerial()
        while(True):
##            self.preaderLocal = self.parent.initSerial()
            print '     Siempre leyendo aca'
#            self.out = ''
            self.out = self.preaderLocal.readline()
            if (self.out != ""):
                print '#############################'
                ok = self.parent.cobrar(self.out, self.preaderLocal)
##              self.preaderLocal.close()
                print 'Respuesta del cobro', ok
                senial = self.emit(self.signal, ok)
                print 'Termine la primer senial'
                #el sleep de tres es para la Pi
                #time.sleep(3)
                #time.sleep1)
                #time.sleep(8)
                self.emit(self.signal2)
                print 'Termine la segunda senial'
##              self.preaderLocal = self.parent.initSerial()
                print '#############################'



class mainWin(QtGui.QMainWindow):
    def __init__(self):
        super(mainWin, self).__init__()
        self.dir = os.path.dirname(__file__)
        self.cdDb = os.path.join(self.dir, 'data/db/tarifas')
        self.openDBAforo = os.path.join(self.dir,'data/db/aforo')
        self.openDBFotos = os.path.join(self.dir,'data/db/existeFoto')
        #self.openDBEV2 = os.path.join(self.dir,'data/db/ev2')
        #Definicion de variables globales
        self.retardo = 1
        self.intervaloTiempoParaInFin = 5
        self.nVuelta = 0

       
        self.inicioFinUno = 'empezando'
        self.inicioFinActual = 'empezando'
        self.banderaIngreso  = 1
        self.valoresCard = {}
        self.versionOS = '0.10'
        self.turnoIniciadoFlag = False
        self.ser = serial.Serial(self.sPort3G, self.velocidad, timeout=1)

        self.initUI()
        self.hora = reloj(self)
        self.modem = inicioGPS(self, self.ser, self.flGPS, self.noGPS)
        self.tresg = TresG(self, self.ser, self.modem)
        self.funcCore = funciones(self)
        self.funcCore.datosVuelta        

        self.esS = escucharSerial(self, self.funcCore)
        self.esS.daemon = True
        self.connect(self.esS, self.esS.signal, self.funcCore.mostrarFoto)
        self.connect(self.esS, self.esS.signal2, self.funcCore.borrarFoto)
        self.esS.start()
        
        #self.obj = rwsGPS(self)
        self.modem.daemon = True
        self.modem.start()


    def initSerial(self):
        print '*****************************************Iniciando puerto serie'
        self.ser = serial.Serial(self.sPort, self.velocidad)
        self.ser.flushInput()
        self.ser.flushOutput()
        return self.ser

    def initSerialEsperandoOK(self):
        print '*******************************Iniciando puerto esperando el OK'
        self.ser = serial.Serial(self.sPort, self.velocidad, timeout = 1)
        self.ser.flushInput()
        self.ser.flushOutput()
        return self.ser

    def closeSerial(self):
        print '****************************************Cerrando el puerto serie'
        self.ser.close()




    def procesoDeEnvio(self, dato, idActualizar, accion, salgo):
    
        print '###       Proceso de envio de datos       ###'
        salirEnvio = 0
        self.evento = accion
        enviado = 0

        while(salgo != 1):
            print 'Cuanto vale', salirEnvio
            print "Dato: "+dato

            
            cmd = 'AT+QISEND=0\r'
            self.ser.write(cmd.encode())
            stRead = ""
            while (stRead[-5:] != "ERROR") and (stRead[-9:] != "SEND FAIL") and (stRead[-7:] != 'SEND OK') and (stRead[-1:] != ">") and (stRead[-18:] != '+QIURC: "closed",0'):
                #print "read"
                stRead += str(self.ser.read(1))
            #print "QISEND: "+stRead
            if (stRead[-5:] == "ERROR") or (self.iComm == 5):
                self.flRedOK = False
                self.flComm = False
                self.iComm = 0
                print '###  Error Conexion con el Servidor. Reinic ###'
                salgo = 1
            elif (stRead[-1:] == ">"):
                self.ser.write(dato.encode()+"\x1A")
                stRead = ""
                i = 0
                while (i < 3) and (stRead[-8:] != '"recv",0') and (stRead[-5:] != "ERROR") and (stRead[-18:] != '+QIURC: "closed",0'):
                    ch = str(self.ser.read(1))
                    if (len(ch) == 0):
                        i += 1
                    else:
                        stRead += ch                    
                    print "send dato: (",i,") ",stRead
                if (i == 3):
                    self.iComm += 1
                if (stRead[-5:] == "ERROR") or (self.iComm == 5) :
                    self.flRedOK = False
                    self.flComm = False
                    self.iComm = 0
                    print '###  Error Conexion con el Servidor. Reinic 2 ###'
                    salgo = 1
                elif  (stRead[-8:] == '"recv",0'):
    		    cmd = 'AT+QIRD=0\r'
                    self.ser.write(cmd.encode())
                    stRead = ""
                    while (stRead[-2:] != 'OK') and (stRead[-5:] != 'ERROR') and (stRead[-18:] != '+QIURC: "closed",0'):
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
                            print "Lista: ",lista
                            if (lista[2][0] == "1"):
                                salgo = 1
                                enviado = 1
                                #buscar si hay una posible actualizacion
                                if (lista[2].find('@') != -1):
                                    #print 'encontre una actualizacion'
                                    #print lista[3]
                                    try:
                                        #print lista[3].split("@")
                                        dos = lista[2].split("@")
                                        #print dos[1]
                                        #print dos[2]
                                        self.actualizarAlgo = lista[2]
                                    except:
                                        print 'No pude parsear la actualizacion'
                                #else:
                                    #print 'no encontre nada que hacer'
                            else:
                                #print 'No recibi un numero osea que esta fallando la comun'
                                #print salirEnvio
                                salirEnvio += 1
                                if (salirEnvio == 2):
                                    print 'Si es mayor entonces rompo el scrip'
                                    self.reinicioAutomatico = self.reinicioAutomatico + 1
                                    salgo = 1
                                    #enviado = 0
                    else:
                        salgo = 1
                        self.flComm = False
                        #enviado = 0
#                        self.flRedOK = False
#                        self.flRed = False                
                else:
                    salgo = 1
                    self.flComm = False
                    #enviado = 0
#                    self.flRedOK = False
#                    self.flRed = False
#                    self.noRed.setPixmap(QtGui.QPixmap("data/img/noRed.Jpeg"))
                    print '###  Error Recepcion Datos Servidor      ###'
            else:
#                self.flRedOK = False
#                self.noRed.setPixmap(QtGui.QPixmap("data/img/noRed.Jpeg"))
                print '###   Error Conexion con el Servidor     ###'
                salgo = 1
                self.flComm = False
                #enviado = 0
        if(enviado == 1 and int(self.evento)==1):
            #print '###          Actualizando GPS            ###'
            #print "Connect actualizando GPS"  
            print "delete actualizando GPS"  
            connT.execute("DELETE FROM tgps WHERE idPos = ?", (idActualizar,))
	    #print "idActualizar "+idActualizar
            print "commit actualizando GPS"  
            connT.commit()
            #c.close()
            #print "close Connect actualizando GPS"  
            #connT.close()
            #connT = None
            self.reinicioAutomatico = 0
        # Barras


class reloj(QtCore.QThread):
    def __init__(self, parent):
        qtcore.QThread.__init__(self)
        self.parent = parent
        self.mes=["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        self.mostrarHora()
      
    def mostrarHora(self):
        if (time.strftime("%Y") > "2015"):
            self.parent.lblHora.setText(time.strftime("%d/")+self.mes[int(time.strftime("%m"))]+time.strftime("/%Y %H:%M:%S"))
            QtCore.QTimer.singleShot(700, self.mostrarHora)

def main():
    app = QtGui.QApplication(sys.argv)
    ex = mainWin()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
