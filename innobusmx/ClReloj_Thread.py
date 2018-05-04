#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4 import QtCore
import time

class clReloj(QtCore.QThread):
    
    def __init__(self, parent):
        QtCore.QThread.__init__(self)
        self.parent = parent
        self.mes=["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        self.flG = False
        self.flR = True
        
    def run(self):


        #self.noRed = QtGui.QLabel(self.parent)
        #self.noRed.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noRed.Jpeg"))
        #self.noRed.setScaledContents(True)
        #self.noRed.move(770,425)
        #self.noRed.resize(20, 20)

        
        while True:
            self.parent.lblHora.setText(time.strftime("%d/")+self.mes[int(time.strftime("%m"))]+time.strftime("/%Y %H:%M:%S"))
            #self.parent.red.load("/home/pi/innobusmx/data/img/GPS.Jpeg")
            #self.parent.red.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/GPS.png"))
            #self.parent.showStatus()
            #self.emit(QtCore.SIGNAL('showImage(QString)'),"/home/pi/innobusmx/data/img/GPS.Jpeg")
            
            if (self.parent.flGPSOK):
                if (self.flG):
                    if (self.parent.flGPS):
                        self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/GPS.png"))
                        print "'GPS'"
                    else:
                        self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noGPS.png"))
                        print "'NoGPS'"
                    self.flG = False
                else:
                    self.parent.noGPS.setPixmap(QtGui.QPixmap(""))
                    print "''"
                    self.flG = True

            if (self.parent.flRedOK):
#               if (self.flR):
                if (self.parent.flRed):
                    self.parent.noRed.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/3G.png"))
                    print "'3G'"
                else:
                    self.parent.noRed.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/no3G.png"))
                    print "'No3G'"
#                self.flR = False
#            else:
#                self.parent.noRed.setPixmap(QtGui.QPixmap(""))
#                self.flR = True
            
            time.sleep(1)
        #QtCore.QTimer.singleShot(1000, self.mostrarHora)
