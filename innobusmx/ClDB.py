#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sqlite3

class sqLite():
    idTransportista = ""
    idUnidad = ""
    economico = ""
    idRuta  = ""
    urlAPN = ""
    userAPN = ""
    pwdAPN = ""
    urlSocket = ""
    puertoSocket = ""
    urlFTP = ""
    puertoFTP = ""
    userFTP = ""
    pwdFTP = ""
    idOperador = ""

    dbAforo   = sqlite3.connect('/home/pi/innobusmx/data/db/aforo',   check_same_thread = False, isolation_level = None)
    dbGPS  = sqlite3.connect('/home/pi/innobusmx/data/db/gps',  check_same_thread = False, isolation_level = None)
    dbComando  = sqlite3.connect('/home/pi/innobusmx/data/db/comandoComm',  check_same_thread = False, isolation_level = None)
    dbListaNegra = sqlite3.connect('/home/pi/innobusmx/data/db/listaNegra', check_same_thread = False, isolation_level = None)
    dbFoto  = sqlite3.connect('/home/pi/innobusmx/data/db/existeFoto',  check_same_thread = False, isolation_level = None)
    dbAlarma  = sqlite3.connect('/home/pi/innobusmx/data/db/alarmas',  check_same_thread = False, isolation_level = None)
    dbTarifa  = sqlite3.connect('/home/pi/innobusmx/data/db/tarifas',  check_same_thread = False, isolation_level = None)

    def __init__(self):
        c = self.dbAforo.cursor()
        c.execute("SELECT idTransportista, idUnidad, economico, idRutaActual, urlAPN, userAPN, pwdAPN, urlSocket, puertoSocket, urlFTP, puertoFTP, userFTP, pwdFTP FROM parametros")
        data = c.fetchone()
        if data is None:
            print 'No hay parAmetros de configuracIon contacta al administrador'
        else:
            self.idTransportista = data[0]
            self.idUnidad = data[1]
            self.economico = data[2]
            self.idRuta = data[3]
            self.urlAPN = data[4]
            self.userAPN = data[5]
            self.pwdAPN = data[6]
            self.urlSocket = data[7]
            self.puertoSocket = data[8]
            self.urlFTP = data[9]
            self.puertoFTP = data[10]
            self.userFTP = data[11]
            self.pwdFTP = data[12]
            
        c.execute('SELECT idChofer FROM usuario')
        data = c.fetchone()
        if data is None:
            print('No hay parametros de configuracon contacta al administrador')
        else:
            self.idOperador = data[0]
        c.close()
        c = None

        self.tarifa = {}

#        self.dbTarifa.execute("UPDATE tar SET cantidad=415 where nom='01'")
#        self.dbTarifa.execute("UPDATE tar SET cantidad=830 where nom='02'")
#        self.dbTarifa.execute("UPDATE tar SET cantidad=900 where nom='03'")
#        self.dbTarifa.execute("UPDATE tar SET cantidad=415 where nom='04'")
#        self.dbTarifa.commit()
#        self.dbTarifa.close()
#        self.dbTarifa  = sqlite3.connect('/home/pi/innobusmx/data/db/tarifas',  check_same_thread = False, isolation_level = None)


        t = self.dbTarifa.cursor()
        t.execute('SELECT * FROM tar')
        data = t.fetchone()
        while not (data is None):
            self.tarifa[data[0]] = data[1]
#            print data[0], self.tarifa[data[0]]
            data = t.fetchone()

        t.close()
        t = None

        
        '''
        connLn = sqlite3.connect('/home/pi/innobusmx/data/db/listaNegra')
        connLn.execute("DELETE FROM negra")
        connLn.commit()
        connLn.close()

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

        '''



    def insertBitacora(self, stRead):
        self.dbAforo.execute("INSERT INTO inicio (fecha) values (?)",(stRead,))
        self.dbAforo.commit()
        
