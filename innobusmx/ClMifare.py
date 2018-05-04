#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore
import time
import os
from PyQt4 import QtGui

class clMifare(QtCore.QThread):
    
    def __init__(self, parent, clDB, clserial, clquectel):
        #print "RDIF OK"
        QtCore.QThread.__init__(self)
        self.ser = clserial
        self.clDB = clDB
        self.clquectel = clquectel
        self.parent = parent

    def msgError(self, tisc, out):
        self.parent.TISC = tisc
        self.parent.stImgTarjeta = '/home/pi/innobusmx/data/img/'+out+'.jpg'
        self.parent.stMsg = self.out
        time.sleep(1.5)
        self.parent.stImgTarjeta = ''
        self.parent.stMsg = ""                                    
        self.parent.TISC = ''

    def run(self):
      self.preaderLocal = self.ser.initSerial()
      if self.preaderLocal != None:
        print '     Siempre leyendo aca'
        print '#############################'
        while(True):
            self.out = ''
            commOK = True
            try:
                self.preaderLocal.flushInput()
                self.preaderLocal.flushOutput()
                self.out = self.preaderLocal.readline()
            except:
                commOK = False
                self.preaderLocal = self.ser.initSerial()

            #print "(",len(self.out),') out', self.out
            if commOK:    
                if ((len(self.out) == 3) and (self.out.find(".") != -1)):
                    os.system("DISPLAY=:0 xset dpms force on")
                else:
                    if (len(self.out) == 5):
                        out = "001"
                        self.out = self.out[0:3]
                        if ((self.out == "002") or (self.out == "008") or (self.out == "012")):
                            out = "003"                        
                        if (self.out == "004"):
                            out = "002"
                        self.msgError(self.out, out)
                    elif (len(self.out) > 20):
                        ok = self.cobrar(self.out)
                        print 'Respuesta del cobro', ok
                        print 'Termine la primer senial'
                        print '#############################'
                    print '     Siempre leyendo aca'
                    print '#############################'
            else:
                self.ser.setupSerial()
                self.preaderLocal = self.ser.initSerial()
                

    def validarDataEV2(self, data):
        #print "Data", data
        longLis = len(data)
        regreso = {}
        if longLis > 65:
            regreso['error'] = False
            regreso['csn'] = data[1:15]
            regreso['llave'] = data[15:31]
            regreso['nomTipoTar'] = data[31:33]
            regreso['eTarjeta'] = 3
            datos = data[33:56]
            datos = datos.split("*")
            #print "datos: (", len(datos) , ")", datos
            regreso['nombre'] = ""
            regreso['apellido'] = ""
            if (len(datos) == 3):
                regreso['nombre'] = datos[0]
                regreso['apellido'] = datos[1]
            else:
                try:
                    if len(datos) > 3:
                        if (len(datos[0]) > 9):
                            regreso['nombre'] = datos[0][0:9]
                            i = 1
                        else:
                            regreso['nombre'] = datos[0]
                            i = 1
                            while (len(datos) > i) and len(regreso['nombre']+' '+datos[i]) < 10:
                                regreso['nombre'] = regreso['nombre'] + ' ' + datos[i]
                                i += 1
                            regreso['apellido'] = ""
                            if (len(datos) > i):
                                regreso['apellido'] = datos[i]
                                i += 1
                                while (len(datos) > i) and len(regreso['apellido']+' '+datos[i]) < 16:
                                    regreso['apellido'] = regreso['apellido'] + ' ' + datos[i]
                                    i += 1
                    else:
                        regreso['nombre'] = ""
                        regreso['apellido'] = ""
                except:
                        regreso['nombre'] = "."
                        regreso['apellido'] = "."
            regreso['vigencia'] = data[57:63]
            datos = data[64:-1]
            datos = datos.split("*")
            regreso['idTipoTarjeta'] = datos[0]
            regreso['saldo'] = datos[1]
            regreso['folio'] = datos[2]
            regreso['saldoV'] = datos[3]
            regreso['tarifa'] = datos[4]
        else:
            regreso['error'] = True
        return regreso


    def validarListaNegra(self, csnS):
        c = self.clDB.dbListaNegra.cursor()
        c.execute("SELECT csn FROM negra WHERE csn = ?", (csnS, ))
        data = c.fetchone()
        c.close
        c = None
        return not (data is None)

    def algunError(self, numError):
        print 'Enviando codigo de cancelacion de transaccion'
        #self.preaderLocal.write('9999999')
        aforoExitoso = 1
        while(aforoExitoso == 1):
            try:
                exito = self.preaderLocal.readline()
            except:
                exito = "N0"
            print 'Esperando el NO'
            esperaRespuesta = 0
            esperaRespuesta = esperaRespuesta + 1
            for c in exito:
                if c == '\n':
                    print 'Que me regresa el validador'
                    rExito = list(exito)
                    print(rExito)
                    if(rExito[0] == 'N' and rExito[1] == 'O'):
                        print 'Recibi el NO por serial'
                        print 'No hago nada solo ceere bien la transaccion'
                        aforoExitoso = 2
                    else:
                        print 'No se hizo la transacion aviar al usuario del aforo normal'
                        aforoExitoso = 2
                        print 'Suelto el hanger'


    def parsearSaldoCobrar(self, saldo):
        while (len(saldo) < 7):
            saldo = "0" + saldo
        #print "saldo: ", saldo
        self.preaderLocal.write(saldo+'\n')
        stRead = ""
        try:
            stRead = self.preaderLocal.readline()
        except:
            stRead = "020"
        print 'Que me regresa el validador?', stRead
        if stRead.find("OK") != -1:
            folio = int(self.valoresCard.get("folio")) + 1
            fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")
            self.clquectel.aforo = True
#            self.clquectel.aforo += '3,'+str(self.valoresCard.get("nomTipoTar"))+','+str(self.clDB.idUnidad)+','+str(self.clDB.idOperador)+','+str(self.valoresCard.get("csn"))+','+saldo+','+str(self.clDB.tarifa[self.valoresCard.get("tarifa")])+','+str(folio)+','+fechaHora+'\r'
#            self.clDB.dbAforo.execute("INSERT INTO validador(idTipoTisc, idUnidad, idOperador, csn, saldo, tarifa, fechaHora, folios, enviado) values (?, ?, ?, ?, ?, ?, ?, ?, 0)", (tipoS, self.clDB.idUnidad, self.clDB.idOperador, csnS, nuevoSaldo, tarifaC, fechaHora, str(folio)))
#            self.clDB.dbAforo.commit()
#            stAforo = '3,'+str(tipoS)+','+str(self.clDB.idUnidad)+','+str(self.clDB.idOperador)+','+str(csnS)+','+str(nuevoSaldo)+','+str(tarifaC)+','+str(folio)+','+fechaHora+'\r'
            #print "stAforo: ",self.clquectel.aforo
#            stAforo = self.clquectel.sendData(stAforo)
#            print "resp: ",stAforo
#            stAforo = "";
#            if stAforo == "":
            fl = True
            while fl:
                try:
                    self.clDB.dbAforo.execute("INSERT INTO validador(idTipoTisc, idUnidad, idOperador, csn, saldo, tarifa, fechaHora, folios, enviado) values (?, ?, ?, ?, ?, ?, ?, ?, 0)",(str(self.valoresCard.get("nomTipoTar")), self.clDB.idUnidad, self.clDB.idOperador, str(self.valoresCard.get("csn")), saldo, self.clDB.tarifa[self.valoresCard.get("tarifa")], fechaHora, str(folio)))
                    self.clDB.dbAforo.commit()
                    fl = False
                    self.clquectel.aforo = True
                except:
                    print "error en el insert del Aforo"
            return True
        else:
            print 'No se hizo la transacion avisar al usuario del aforo normal'
            self.msgError(stRead, "001")
            return False


    def cobrar(self, datos):
        print 'Empiezo el proceso de cobro'
        numError = 0
        no = 'NO,NV,S*S,1'
        if datos:
            if datos[0] == "3":
                print 'Es EV2'
                self.valoresCard = self.validarDataEV2(datos)
                if self.valoresCard['error']:
                    numError = 3
                else:
                    if self.validarListaNegra(self.valoresCard.get("csn")):
                        numError = 3
                    else:
                        if (self.valoresCard.get("tarifa") != "00"):
                            try:
                                print self.clDB.tarifa[self.valoresCard.get("tarifa")]
                            except:
                                numError = 2
                                print 'Tarifa no existe en el sistema no se puede cobrar'
                            if (numError == 0):
                                saldo = int(self.valoresCard.get('saldo'))+int(self.valoresCard.get('saldoV'))
                                #print "Saldo:",saldo - self.clDB.tarifa[self.valoresCard.get("tarifa")], "=", saldo, " - ", self.clDB.tarifa[self.valoresCard.get("tarifa")]
                                if (saldo < int(self.clDB.tarifa[self.valoresCard.get("tarifa")])):
                                    #print saldo," - "
                                    numError = 4
                                    no = 'NO,SS,S*S,%s'%str(saldo)
                                    saldo = saldo / 100.0
                                    self.parent.stSaldoInsuficiente = str("$ %.2f" % saldo)                                    
                                else:
                                    saldo = saldo - self.clDB.tarifa[self.valoresCard.get("tarifa")]
                                    if self.parsearSaldoCobrar(str(saldo)):
                                        path = '/home/pi/innobusmx/data/user/'+self.valoresCard.get("csn")[0:5]+"/"+self.valoresCard.get("csn")+".Jpeg"
                                        if os.path.isfile(path):
                                            self.parent.TISC = '/home/pi/innobusmx/data/user/'+self.valoresCard.get("csn")[0:5]+"/"+self.valoresCard.get("csn")+".Jpeg"
                                        else:
                                            self.parent.TISC = '/home/pi/innobusmx/data/user/generico.jpg'
                                        saldo = saldo / 100.0
                                        self.parent.stImgTarjeta = '/home/pi/innobusmx/data/img/imgTarjetas/'+self.valoresCard.get("nomTipoTar")+'.jpg'
                                        self.parent.stSaldo = str("$ %.2f" % saldo)
                                        self.parent.stNombre = self.valoresCard.get("nombre")
                                        self.parent.stApellido = self.valoresCard.get("apellido")
                                        #print "nombre: ", self.valoresCard.get("nombre")
                                        time.sleep(1.5)
                                        self.parent.stImgTarjeta = ''
                                        self.parent.TISC = ""
                                        self.parent.stSaldo = ""
                                        self.parent.stNombre = ""
                                        self.parent.stApellido = ""
                                        return "OK"
                        else:
                    
                                if(self.valoresCard.get("nomTipoTar") == 'KI'):
                                    #print 'Es un pinche chofi chofi'
                                    nombre = self.valoresCard.get("nombre") + " " + self.valoresCard.get("apellido")
                                    #self.ser = self.initSerial()
                                    respuesta = self.inicioFinVueltaChofer(self.valoresCard.get("csn"), nombre)
                                    #print 'Respuesta de abajo', respuesta
                                    numError = 4
                                    self.algunError(numError)
                                    #self.closeSerial()
                                    
                                    #conn = sqlite3.connect(self.openDBAforo)
                                    c = self.clDB.dbAforo.cursor()
                                    c.execute("SELECT nombre FROM configuraSistema, ruta WHERE idRutaActual = id")
                                    data = c.fetchone()
                                    if data is None:
                                        self.lblRuta.setText("")
                                    else:
                                        self.lblRuta.setText(data[0])
                                    c.close
                                    #conn.close
                                    
                                    no = '%s,O,S*S,%s,%s'%(self.valoresCard.get("csn"), str(respuesta), nombre)
                                    #no = 'NO,O,S*S,'
                                    return no
                                if(self.valoresCard.get("nomTipoTar") == 'AN'):
                                    #self.ser = self.initSerial()
                                    respuesta = self.mostrarAforosOInicioFinTurno(self.valoresCard.get("csn"))
                                    print 'Respuesta de abajo', respuesta
                                    numError = 4
                                    self.algunError(numError)
                                    #self.closeSerial()
                                    nombre = self.valoresCard.get("nombre") + " " + self.valoresCard.get("apellido")
                                    #no = 'NO,A%s,S*S,1'%str(respuesta)
                                    no = 'NO,A,S*S,%s,%s'%(str(respuesta), nombre)
                                    return no
                                
        if ((numError != 0) or (datos[0] != "3")):
            
                self.parent.stImgTarjeta = '/home/pi/innobusmx/data/img/00'+str(numError)+'.jpg'
                self.parent.TISC = '/home/pi/innobusmx/data/user/0.jpg'
                time.sleep(1.5)
                self.parent.TISC = ''
                self.parent.stImgTarjeta = ''
                self.parent.stSaldoInsuficiente = ""                                    
                print 'No hago nada' , numError
                #self.algunError(numError)
                no = 'NO,VAI,S*S,1'
                return no
        print 'Termine el proceso de pago'
        return True



    
                        #self.algunError(numError)
                        #self.preaderLocal.write('9999999')            
                        #return no
























    def mostrarFoto(self, sigstr):
        pathdir = os.path.dirname(__file__)
        print "Mostrar Foto ",sigstr
        if not isinstance(sigstr,bool):
#        try:
            #DAACD9C7,ES,don**vergas*u8o,959
            #print sigstr.split(",")
            dos = sigstr.split(",")
            #print dos[0]
            #print dos[1]
            #print dos[2]
            nombre = dos[2].split("*")
            #print nombre[0]
            #print nombre[1]
            saldo = dos[3]
            #print saldo
            try:
                nombreOperador = dos[4]
            except:
                print 'ni peiper'

            print dos[1]

            if dos[1] == 'EV2':
                print 'Poner lo que va en pantalla'
                self.parent.lblVAI.setText("Eres una EV2 :D")
                imgTarjetaAtras = "data/img/error.png"
                scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
            if dos[1] == 'AP':
                self.parent.close()
            if dos[1] == 'SS':
                imgTarjetaAtras = "data/img/error.png"
                scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                #print 'Sin saldo'
                self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                #self.parent.lblSS.setText("Sin saldo")
                print 'Aqui esta el saldo como llega'
                print saldo
                self.parent.lblSS.setText("Sin saldo")
                saldoInt = int(saldo)
                nuevoSaldoP = float(saldoInt)/100
                print 'Aqui esta el saldo transformado'
                print nuevoSaldoP
                #elf.SA.setText(str("%.2f" % saldoPesos))
                mensaje = 'Saldo actual: $ %.2f'%(nuevoSaldoP)
                self.parent.lblSSMsg.setText(mensaje)
                QtGui.qApp.processEvents()

            if dos[1] == 'VAI':
                imgTarjetaAtras = "data/img/error.png"
                scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                #print 'Sin saldo'
                self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                self.parent.lblVAI.setText("Intenta de nuevo")
                QtGui.qApp.processEvents()

            if dos[1] == 'NV':
                imgTarjetaAtras = "data/img/error.png"
                scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                #print 'Sin saldo'
                self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                #self.parent.lblVAI.setText("No valida")
                self.parent.lblNV.setText("No Valida")
                QtGui.qApp.processEvents()

            if dos[1] == 'A':
                if saldo == "1":
                    if self.parent.turnoIniciadoFlag == False:
                        imgTarjetaAtras = "data/img/us.jpg"
                        scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                        #print 'Sin saldo'
                        self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                        self.parent.lblVAI.setText("Cuidado puedes alterar")
                        self.parent.lblSSMsg.setText("el turno")
                        QtGui.qApp.processEvents()
                    if self.parent.turnoIniciadoFlag == True:
                        #conn = sqlite3.connect(self.parent.openDBAforo)
                        c = self.clDB.dbAforo.cursor()
                        c.execute("SELECT inicioFin, fechaHora FROM soloVuelta ORDER BY idSoloVuelta DESC LIMIT 1")
                        fechaHoraUltimaVuelta = c.fetchone()
                        fechahoraInicio = fechaHoraUltimaVuelta[1]
                        print fechahoraInicio
                        #Consulta que me devuelve si hay o no un turno iniciado
                        c.execute("SELECT idTipoTisc, Count(idTipoTisc)   FROM validador WHERE fechaHora BETWEEN ? AND DATETIME('now') GROUP BY idTipoTisc",(fechahoraInicio,))
                        data = c.fetchall()
                        print 'Aca estan los datos de la consulta'
                        print data

                        transData = str(data).encode('ascii','ignore')
                        nstr = re.sub(r'[?|$|.|!|u]',r'',str(transData))
                        nestr = re.sub(r'[^a-zA-Z0-9 ]',r'',nstr)
                        print nestr

                        imgTarjetaAtras = "data/img/us.jpg"
                        scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                        #print 'Sin saldo'
                        self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                        self.parent.lblVAI.setText("Cuidado puedes alterar")
                        self.parent.lblSSMsg.setText("el turno")
                        self.parent.lblTarjetas.setText(str(nestr))
                        QtGui.qApp.processEvents()
                if saldo == "21":
                    imgTarjetaAtras = "data/img/us.jpg"
                    scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                    #print 'Sin saldo'
                    self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                    self.parent.lblVAI.setText("Turno iniciado")
                    self.parent.turnoIniciadoFlag = True
                    QtGui.qApp.processEvents()
                if saldo == "11":
                    if self.parent.turnoIniciadoFlag == False:
                        imgTarjetaAtras = "data/img/us.jpg"
                        scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                        #print 'Sin saldo'
                        self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                        self.parent.lblVAI.setText("Inicio de turno")
                        self.parent.lblSSMsg.setText("cancelado")
                        QtGui.qApp.processEvents()
                    if self.parent.turnoIniciadoFlag == True:
                        #conn = sqlite3.connect(self.parent.openDBAforo)
                        c = self.clDB.dbAforo.cursor()
                        c.execute("SELECT inicioFin, fechaHora FROM soloVuelta ORDER BY idSoloVuelta DESC LIMIT 1")
                        fechaHoraUltimaVuelta = c.fetchone()
                        fechahoraInicio = fechaHoraUltimaVuelta[1]
                        print fechahoraInicio
                        #Consulta que me devuelve si hay o no un turno iniciado
                        c.execute("SELECT idTipoTisc, Count(idTipoTisc)   FROM validador WHERE fechaHora BETWEEN ? AND DATETIME('now') GROUP BY idTipoTisc",(fechahoraInicio,))
                        data = c.fetchall()
                        print 'Aca estan los datos de la consulta'
                        print data
                        transData = str(data).encode('ascii','ignore')
                        nstr = re.sub(r'[?|$|.|!|u]',r'',str(transData))
                        nestr = re.sub(r'[^a-zA-Z0-9 ]',r'',nstr)
                        print nestr

                        imgTarjetaAtras = "data/img/us.jpg"
                        scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                        #print 'Sin saldo'
                        self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                        self.parent.lblVAI.setText("Inicio de turno")
                        self.parent.lblSSMsg.setText("cancelado")
                        self.parent.lblTarjetas.setText(str(nestr))
                        QtGui.qApp.processEvents()
                if saldo == "3":
                    imgTarjetaAtras = "data/img/us.jpg"
                    scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                    #print 'Sin saldo'
                    self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                    self.parent.lblVAI.setText("Turno")
                    self.parent.lblSSMsg.setText("Finalizado")
                    self.parent.turnoIniciadoFlag = False
                    QtGui.qApp.processEvents()
            if dos[1] == 'O':
                if saldo == "1":
                    imgTarjetaAtras = "data/img/chofer.bmp"
                    scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                    #print 'Sin saldo'
                    self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                    self.parent.lblInFinVuelta.setText("Finalizando Vuelta")
                    #self.parent.lblVAI.setText("Finalizando")
                    #self.parent.lblSSMsg.setText("Vuelta")

                    self.parent.lblOperador.setPixmap(QtGui.QPixmap(""))
                    self.parent.lblRuta.setText("")
                    self.parent.lblNombreOperador.setText("")
                    self.parent.lblVuelta.setText("")

                    QtGui.qApp.processEvents()
                if saldo == "2":
                    imgTarjetaAtras = "data/img/chofer.bmp"
                    scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                    self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))

                    #self.parent.lblVAI.setText("Iniciando")
                    #self.parent.lblSSMsg.setText("Vuelta")
                    self.parent.lblInFinVuelta.setText("Iniciando Vuelta")

#                    imgChofer = "data/user/chofer.jpg"
                    imgChofer = "data/user/%s.Jpeg"%dos[0]
                    scriptChofer = os.path.join(pathdir, imgChofer)
                    self.parent.lblOperador.setPixmap(QtGui.QPixmap(scriptChofer))
                    print scriptChofer
                    print dos

#                    self.parent.lblRuta.setText(dos[5])
                    self.parent.lblNombreOperador.setText(str(nombreOperador))
                    self.parent.lblVuelta.setText(str(self.parent.nVuelta))

                    QtGui.qApp.processEvents()
                if saldo == "3":
                    imgTarjetaAtras = "data/img/us.jpg"
                    scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                    #print 'Sin saldo'
                    self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                    self.parent.lblVAI.setText("No hay turno")
                    self.parent.lblSSMsg.setText("iniciado")
                    QtGui.qApp.processEvents()
            else:
                if dos[0] ==  'NO':
                    print 'No hagas nada con la foto'
                else:
                    saldoInt = int(saldo)
                    nuevoSaldoP = float(saldoInt)/100
                    filename = 'data/user/%s.Jpeg'%dos[0]
                    print 'Estoy aqui adentro de descargar la foto', filename
                    scriptImgBusqueda = os.path.join(pathdir, filename)
                    print scriptImgBusqueda
                    if os.path.exists(scriptImgBusqueda):
                        print 'La foto existe la voy a procesar'
                        imgTarjetaAtras = "data/img/imgTarjetas/%s.jpg"%dos[1]
                        imgUsuarioTarjeta = "data/user/%s.Jpeg"%dos[0]

                        '''
                        #print 'Imprimo los nombres de las dos variables'
                        #print imgTarjetaAtras
                        #print imgUsuarioTarjeta
                        scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                        scriptPathTarjeta = os.path.join(pathdir, imgUsuarioTarjeta)
                        #print 'Imprimo las dos variables completas donde voy a busccar las fotos'
                        #print scriptPathTarjeta
                        #print scriptPathAtras
                        self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                        self.parent.imgDefault.setPixmap(QtGui.QPixmap(scriptPathTarjeta))
                        self.parent.lblNombreApe.setText(str(nombre[0]))
                        self.parent.lblSaldo.setText(str("$ %.2f" % nuevoSaldoP))
                        QtGui.qApp.processEvents()
                        '''
                        #print 'Lo termine bien'
                    else:
                        print 'La foto no existe'
                        self.parent.TISC = "/home/pi/innobusmx/data/user/generico.jpg"
                        

                        #try:
                        #    urllib.urlretrieve('ftp://innogps:inno@192.168.1.8/Fotos/'+dos[0]+'.Jpeg', filename)
                        #    fotoD = 1
                        #except:
                        #   print 'No hemos podido descargar la foto'
                        #    if fotoD == 1:
                                #print 'Ya descargue la foto aca  voy a mostrar'
                                #print 'Esto lo paso como parametro'
                                #print sigstr
                                #self.parent.mostrarFoto(sigstr)
                                #self.parent.emit(self.parent.signal, sigstr)
                                #print 'Como ya la tengo ahora la voy a mostrar sin recursion'
                                #print '*******nueva manera***************'
                        imgTarjetaAtras = "data/img/imgTarjetas/%s.jpg"%dos[1]
                        #imgUsuarioTarjeta = "data/user/admin.png"
                        imgUsuarioTarjeta = "data/user/adminis.jpg"
                                #print 'Imprimo los nombres de las dos variables'
                                #print imgTarjetaAtras
                                #print imgUsuarioTarjeta
                        scriptPathAtras = os.path.join(pathdir, imgTarjetaAtras)
                        scriptPathTarjeta = os.path.join(pathdir, imgUsuarioTarjeta)
                                #print 'Imprimo las dos variables completas donde voy a busccar las fotos'
                                #print scriptPathTarjeta
                                #print scriptPathAtras

                        '''
                        self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                        self.parent.imgDefault.setPixmap(QtGui.QPixmap(scriptPathTarjeta))
                        self.parent.lblNombreApe.setText(str(nombre[0]))
                        self.parent.lblSaldo.setText(str("$ %.2f" % nuevoSaldoP))
                        QtGui.qApp.processEvents()
                                #ser.close()
                                #print 'Lo termine bien'
                        '''
                        salgo = 1
                        print '###         Muestro imagen generica      ###'

                    self.parent.muestraCredencial(scriptPathAtras, scriptPathTarjeta, str(nombre[0]), str("$ %.2f" % nuevoSaldoP))
                    return True

                        
#        except:
#           print 'Error al parsear los datos de la foto'

    def borrarFoto(self):
        #print 'La voy a quitar de pantalla'
        self.parent.lblNombreApe.setText("")
        self.parent.lblSaldo.setText("")
        self.parent.lblSS.setText("")
        self.parent.lblVAI.setText("")
        self.parent.lblSSMsg.setText("")
        self.parent.imgDefault.setPixmap(QtGui.QPixmap(""))
        #self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(""))
        self.parent.lblTarjetas.setText("")
        self.parent.lblNV.setText("")
        self.parent.lblInFinVuelta.setText("")
        QtGui.qApp.processEvents()


        

    def inicioFinVueltaChofer(self, csn, stOperador):
        #self.ser = ser
        #funcion que inicia o termna un recorrido
        #conn = sqlite3.connect(self.openDBAforo)
        c = self.clDB.dbAforo.cursor()
        #Validar si hay una vuelta iniciada o no
        fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")
        c.execute("SELECT idUnidad, kmActual FROM configuraSistema");
        datosSistema = c.fetchone()

        if datosSistema is None:
            print('No existen datos de configuracion del sistema')
        else:
            print('Si existen los datos necesaios del sistema')
            idUni = datosSistema[0]
            kmAct = datosSistema[1]

        #voy a buscar si hay turno iniciado si no no inicio
        c.execute("SELECT inicioFin FROM turnoDelDia ORDER BY idTurnoDelDia DESC LIMIT 1")
        turno = c.fetchone()

        if turno[0] == 'I':
            #busco si la vuelt esta iniciada o terminada si esta iniciada me decuelte un I
            #por lo cual la voy a finzalizar
            # si me devuelve una F la voy a iniciar
            c.execute("SELECT inicioFin FROM soloVuelta ORDER BY idSoloVuelta DESC LIMIT 1")
            data = c.fetchone()

            if data[0] == 'I':
                print 'Voy a finalizar'
                #self.lblTN.setText('Finalizando')
                #self.lblTNV.setText('vuelta')
                c.execute("SELECT km, csn, num_vuelta FROM soloVuelta ORDER BY idSoloVuelta DESC LIMIT 1")
                data = c.fetchone()
                if data is None:
                    print 'No hay vueltas antes'
                else:
                    km = data[0]
                    csnA  = data[1]
                    nVuelta = data[2]
                c.execute("SELECT idUnidad, idRutaActual FROM configuraSistema")
                ruta = c.fetchone()
                if ruta is None:
                    print 'No hay vueltas antes'
                else:
                    iUnidad = ruta[0]
                    ruta = ruta[1]
                c.execute("SELECT kmEstimado FROM ruta WHERE id = ?", (ruta, ))
                kmE = c.fetchone()
                if kmE is None:
                    print 'kmEstimado no se encuentra'
                else:
                    kmS = kmE[0]
                    
                kmNuevo = int(km) + int(kmS)
                c.execute("SELECT turno FROM turnoDelDia ORDER BY idTurnoDelDia DESC LIMIT 1")
                turno = c.fetchone()
                if turno is None:
                    print 'No hay turnos'
                else:
                    turnoA = turno[0]
                #INSERT INTO soloVuelta(fechahora, km, idUnidad, csn, num_vuelta, turno, inicioFin, enviados) VALUES(?, ?, ?, ?, ?, ?,? ,?), ('esta-siempre-va', 0, 0, 00000000, 0, 'M','F', 1);
                c.execute("INSERT INTO soloVuelta(fechahora, km, idUnidad, idRuta, csn, num_vuelta, turno, inicioFin, enviados) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (fechaHora, kmNuevo, iUnidad, ruta, csn, nVuelta, turnoA, 'F', 0))
                self.clDB.dbAforo.commit()
                #actualizo el kilometraje de la unidad despues de la vuelta
                c.execute("UPDATE configuraSistema SET kmActual = ?, operador = ''",(kmNuevo, ))
                self.clDB.dbAforo.commit()
                numError = 4
                return 1
                #self.algunError(numError, self.ser)
            if data[0] == 'F':
                print 'Voy a iniciar'
                print 'Iniciando vuelta'
                #self.lblTN.setText('Iniciando')
                #self.lblTNV.setText('vuelta')
                '''
                    #########################################################
                        Antes de iniciar vuelta debo de conocer si hay una
                        vuelta iniciada el dia de hoy si hay una vuelta debo
                        de obtener el numero de vuelta actual y sumarle uno
                        si no hay vuelta de hoy iniciare un nuevo conteo de
                        vuelta.
                    #########################################################
                '''
                c.execute("SELECT km, csn, num_vuelta, fechahora FROM soloVuelta ORDER BY idSoloVuelta DESC LIMIT 1")
                data = c.fetchone()
                if data is None:
                    print 'No hay vueltas antes'
                else:
                    km = data[0]
                    csnA  = data[1]
                    nVuelta = data[2]
                    fecha = data[3]

                c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                data = c.fetchone()
                if data is None:
                    print('No hay parametros de configuracon contacta al administrador')
                else:
                    idUni = data[0]
                    idRuta = data[1]

                c.execute("SELECT turno FROM turnoDelDia ORDER BY idTurnoDelDia DESC LIMIT 1")
                turno = c.fetchone()
                if turno is None:
                    print 'No hay turnos'
                else:
                    turnoA = turno[0]

                print fecha
                fechaF = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
                print fechaF
                if fechaF.date() == datetime.today().date():
                    print 'Si hay vueltas inicidas antes'
                    self.nVuelta = int(nVuelta) + 1
                    c.execute("INSERT INTO soloVuelta(fechahora, km, idUnidad, idRuta, csn, num_vuelta, turno, inicioFin, enviados) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (fechaHora, kmAct, idUni, idRuta, csn, self.nVuelta, turnoA, 'I', 0))
                    self.clDB.dbAforo.commit()
                else:
                    #nVueltaNueva = int(nVuelta) + 1
                    print 'Error en la validaciop'
                    c.execute("INSERT INTO soloVuelta(fechahora, km, idUnidad, idRuta, csn, num_vuelta, turno, inicioFin, enviados) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (fechaHora, kmAct, idUni, idRuta, csn, 1, turnoA, 'I', 0))
                    self.clDB.dbAforo.commit()

                c.execute("UPDATE configuraSistema SET operador = ?",(stOperador, ))
                self.clDB.dbAforo.commit()

                numError = 4
                return 2
                #self.algunError(numError, self.ser)

        if turno[0] == 'F':
            #self.lblTN.setText('No hay turno iniciado')
            print 'No hay turno inciado'
            numError = 4
            return 3
            #self.algunError(numError, self.ser)
        #conn.close

    def mostrarAforosOInicioFinTurno(self, csn):
            '''
                ##############################################################
                    Funcion que muestra aforos si hay una vuelta iniciada
                    o inicia o termina turno.
                ##############################################################
            '''
            respuesta = 0;
            #self.ser = ser
            #conn = sqlite3.connect(self.openDBAforo)
            c = self.clDB.dbAforo.cursor()

            #Consulta que me devuelve si hay o no un turno iniciado
            c.execute("SELECT fechaHora, turno, inicioFin  FROM \
                turnoDelDia WHERE date('now')=date(fechaHora) ORDER BY \
                idTurnoDelDia DESC LIMIT 1")
            data = c.fetchone()
            if data is None:
                print 'No hay turno iniciado'
                #Valido si hay un paso de tarjeta anterior para ver si quiere cerrar el turno
                c.execute("SELECT id, fechahora FROM inicioFinTurno")
                hayDato = c.fetchone()
                if hayDato is None:
                    print 'Es la primera la guardo'
                    tiempoActual = time.strftime("%H:%M:%S")
                    c.execute("INSERT INTO inicioFinTurno(fechahora) VALUES(?)", (tiempoActual,))
                    self.clDB.dbAforo.commit()
                    respuesta = 1;
                else:
                    print 'Ya hay un tiempo anterior'
                    #Como se que es el primero del dia simplemente asigno
                    #el turno numero uno del dia, de igual manera es un inicio
                    turnoLocal = 1
                    inFin = "I"
                    tiempoAnterior = hayDato[1]
                    FMT = '%H:%M:%S'
                    tiempoActual = time.strftime("%H:%M:%S")
                    fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")
                    tdelta = datetime.strptime(tiempoActual, FMT) - datetime.strptime(tiempoAnterior, FMT)
                    print 'Esta es la diferencia de tiempos'
                    print tdelta.seconds
                    if tdelta.seconds <= self.intervaloTiempoParaInFin:
                        print 'Voy a iniciar turno'
                        print 'Eliminando tiempos para que quede limpia'
                        idBorrar = hayDato[0]
                        c.execute("DELETE FROM inicioFinTurno WHERE id = ?", (idBorrar, ))
                        self.clDB.dbAforo.commit()
                        print 'Registro Borrado'
                        c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                        data = c.fetchone()
                        if data is None:
                            print('No hay parametros de configuracon contacta al administrador')
                        else:
                            idUni = data[0]
                            idRuta = data[1]
                        c.execute("INSERT INTO turnoDelDia(fechahora, idUnidad, \
                        idRuta, csn, turno, inicioFin, enviados) \
                        VALUES(?, ?, ?, ?, ?, ?, ?)", (fechaHora, idUni, \
                        idRuta, csn, turnoLocal, inFin, 0))
                        self.clDB.dbAforo.commit()
                        respuesta =  21
                    #esto pasa cuando ya hay un tiempo y es mas la diferencia
                    #entr tiempos asi que los voy a eliminar
                    else:
                        print 'Eliminando tiempos'
                        idBorrar = hayDato[0]
                        c.execute("DELETE FROM inicioFinTurno WHERE id = ?", (idBorrar, ))
                        self.clDB.dbAforo.commit()
                        print 'Registro Borrado'
                        respuesta = 11
            else:
                turno = data[1]
                print 'Si hay un turno iniciado'
                #Valido si hay un paso de tarjeta anterior para ver si quiere cerrar el turno
                c.execute("SELECT id, fechahora FROM inicioFinTurno")
                hayDato = c.fetchone()
                if hayDato is None:
                    print 'Es la primera la guardo'
                    tiempoActual = time.strftime("%H:%M:%S")
                    c.execute("INSERT INTO inicioFinTurno(fechahora) VALUES(?)", (tiempoActual,))
                    self.clDB.dbAforo.commit()
                    respuesta = 1
                else:
                    print 'Ya hay un tiempo anterior'
                    #Como se que es el primero del dia simplemente asigno
                    #el turno numero uno del dia, de igual manera es un inicio
                    turnoLocal = 1
                    inFin = "F"
                    tiempoAnterior = hayDato[1]
                    FMT = '%H:%M:%S'
                    tiempoActual = time.strftime("%H:%M:%S")
                    fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")
                    tdelta = datetime.strptime(tiempoActual, FMT) - datetime.strptime(tiempoAnterior, FMT)
                    print 'Esta es la diferencia de tiempos'
                    print tdelta.seconds
                    if tdelta.seconds <= self.intervaloTiempoParaInFin:
                        print 'Voy a cerrar turno'
                        print 'Eliminando tiempos para que quede limpia'
                        idBorrar = hayDato[0]
                        c.execute("DELETE FROM inicioFinTurno WHERE id = ?", (idBorrar, ))
                        self.clDB.dbAforo.commit()
                        print 'Registro Borrado'
                        #lo que voy a hacer aca es que si el turno anterior es un
                        #inicio solo lo voy a finalizar tal cual
                        if data[2] == 'I':
                            c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                            data = c.fetchone()
                            if data is None:
                                print('No hay parametros de configuracon contacta al administrador')
                            else:
                                idUni = data[0]
                                idRuta = data[1]

                            c.execute("INSERT INTO turnoDelDia(fechahora, idUnidad, \
                            idRuta, csn, turno, inicioFin, enviados) \
                            VALUES(?, ?, ?, ?, ?, ?, ?)", (fechaHora, idUni, \
                            idRuta, csn, turno, inFin, 0))
                            self.clDB.dbAforo.commit()
                            respuesta = 3;
                        else:
                        #if data[2] == 'F':
                            turnoNuevo = int(turno) + 1
                            c.execute("SELECT idTurno from tTurno WHERE idTurno = ?", (turnoNuevo,))
                            turnoN = c.fetchone()
                            if turnoN is None:
                                print 'No hay turno siguiente'

                                turnoLocal = 1
                                inFin = "I"
                                fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")

                                c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                                data = c.fetchone()
                                if data is None:
                                    print('No hay parametros de configuracon contacta al administrador')
                                else:
                                    idUni = data[0]
                                    idRuta = data[1]

                                c.execute("INSERT INTO turnoDelDia(fechahora, idUnidad, \
                                idRuta, csn, turno, inicioFin, enviados) \
                                VALUES(?, ?, ?, ?, ?, ?, ?)", (fechaHora, idUni, \
                                idRuta, csn, turnoLocal, inFin, 0))
                                self.clDB.dbAforo.commit()
                                respuesta = 21
                            else:
                                print 'Si hay un turno siguiente'
                                inFin = "I"
                                fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")

                                c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                                data = c.fetchone()
                                if data is None:
                                    print('No hay parametros de configuracon contacta al administrador')
                                else:
                                    idUni = data[0]
                                    idRuta = data[1]

                                c.execute("INSERT INTO turnoDelDia(fechahora, idUnidad, \
                                idRuta, csn, turno, inicioFin, enviados) \
                                VALUES(?, ?, ?, ?, ?, ?, ?)", (fechaHora, idUni, \
                                idRuta, csn, turnoNuevo, inFin, 0))
                                self.clDB.dbAforo.commit()
                                respuesta= 21
                    #no supero el tiempo asi que no lo voy a acabar
                    else:
                        print 'Eliminando tiempos'
                        idBorrar = hayDato[0]
                        c.execute("DELETE FROM inicioFinTurno WHERE id = ?", (idBorrar, ))
                        self.clDB.dbAforo.commit()
                        print 'Registro Borrado'
                        respuesta = 11

            numError = 4
            #conn.close
            return respuesta
            #self.algunError(numError, self.ser)



    def yaPagoAntes(self, tipoS, csnS):
        print 'Validando si ya pago antes'
        enviados = 0
        #conn = sqlite3.connect(self.openDBAforo)
        c = self.clDB.dbAforo.cursor()
        ini = 'I'
        c.execute("SELECT fechaHora FROM soloVuelta WHERE inicioFin=? ORDER BY idSoloVuelta DESC LIMIT 1", (ini,))
        comparar = c.fetchone()
        if comparar is None:
            print 'No hay turno activo el dia de hoy'
        else:
            horaComparar = comparar[0]

        c.execute("SELECT fechaHora FROM validador WHERE csn = ? ORDER BY idValidador DESC LIMIT 1" ,(csnS, ))
        data = c.fetchone()
        if data is None:
            print 'No habias pagado antes'
            return False
        else:
            horaDelPago = data[0]

        FMT = '%Y-%m-%d %H:%M:%S'
        tdelta = datetime.strptime(horaComparar, FMT) < datetime.strptime(horaDelPago, FMT)

        #print 'hora del inicio de turno', horaComparar
        #print 'hora del ultimo pago', horaDelPago

        #Aqui modificare que pueda pagar mas de dos veces cambiando el True del if
        #por un False en el if.
        #conn.close
        if tdelta == True:
            #return True
            return False
        else:
            return False




        
