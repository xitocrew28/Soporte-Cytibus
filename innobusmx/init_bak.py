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
            self.out = ''
            print '#############################'
            self.out = self.preaderLocal.readline()
            ok = self.parent.cobrar(self.out, self.preaderLocal)
##            self.preaderLocal.close()
            print 'Respuesta del cobro', ok
            senial = self.emit(self.signal, ok)
            print 'Termine la primer senial'
            #el sleep de tres es para la Pi
            time.sleep(3)
            #time.sleep(1)
            #time.sleep(8)
            self.emit(self.signal2)
            print 'Termine la segunda senial'
##            self.preaderLocal = self.parent.initSerial()
            print '#############################'


class mainWin(QtGui.QMainWindow):
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



    def cobrar(self, datos, ser):
        print 'Empiezo el proceso de cobro'
        self.datos = datos
        self.ser = ser
        print "Datos: ",self.datos
        if self.datos:
            lista = self.datos.split('*')
            print "Lista: ", lista
            tisc = lista[0]
            csn = lista[1]
            tipoTisc = lista[2]
            if (len(lista) == 9):
                nombre = ""
                paterno = ""
                materno = ""
                vigencia = lista[4]
                tarifa = lista[5]
                folio = lista[6]
                saldo = lista[7]
            else:
                nombre = lista[3]
                paterno = lista[4]
                materno = lista[5]
                vigencia = lista[6]
                tarifa = lista[7]
                folio = lista[8]
                saldo = lista[9]
                
            enListaNegra = self.funcCore.validarListaNegra(csn)
            if tisc == '3':
                print 'Es EV2'
                if tarifa == "00":
                    print "Usuario Sistema"
                    if(tipoTisc == 'KI'):
                        print 'Es un pinche chofi chofi'
                        #nombre = self.valoresCard.get("nombre") + " " + self.valoresCard.get("apellido")
                        self.ser = self.initSerial()
                        chofer = nombre + " " + paterno
                        respuesta = self.inicioFinVueltaChofer(csn, chofer)
                        #print 'Respuesta de abajo', respuesta
                        numError = 4
                        self.algunError(numError, self.ser)
                        self.closeSerial()
                                    
                        conn = sqlite3.connect(self.openDBAforo)
                        c = conn.cursor()
                        c.execute("SELECT nombre FROM configuraSistema, ruta WHERE idRutaActual = id")
                        data = c.fetchone()
                        c.close()
                        if data is None:
                            self.lblRuta.setText("")
                        else:
                            self.lblRuta.setText(data[0])
                        conn.close
                                    
                        return '%s,O,S*S,%s,%s'%(csn, str(respuesta), chofer)
                    if (tipoTisc == 'AN'):
                        self.ser = self.initSerial()
                        respuesta = self.mostrarAforosOInicioFinTurno(self.ser, csn)
                        print 'Respuesta de abajo', respuesta
                        numError = 4
                        self.algunError(numError, self.ser)
                        self.closeSerial()
                        analista = nombre + " " + paterno
                        #no = 'NO,A%s,S*S,1'%str(respuesta)
                        return 'NO,A,S*S,%s,%s'%(str(respuesta), analista)

                else:
                    cobrarTarifa = self.obtenerTarifa(tarifa) 
                    if cobrarTarifa == False:
                        print 'Tarifa no existe en el sistema no se puede cobrar'
                        numError = 1
                        self.ser = self.initSerial()
                        self.algunError(numError, self.ser)
                        sel.closeSerial()
                        return 'NO,NV,S*S,1'
                    else:
                        print 'Tarifa valida en el sistema' 
                        if self.funcCore.saldoSuf(cobrarTarifa, saldo):
                            print 'Iniciando el serial'
                            self.ser = self.initSerial()
                            self.sinSaldo(cobrarTarifa, saldo, self.ser)
                            self.closeSerial()
                            return 'NO,SS,S*S,%s'%str(saldo)
                        else:
                            print 'Saldo suficiente cobrare'
                            nuevoSaldo = int(saldo) - int(cobrarTarifa)
                            print nuevoSaldo, " = ", int(saldo), " - ", int(cobrarTarifa)
                            lonSaldoNuevo = len(str(nuevoSaldo))
                                            
                            print 'Iniciando el Serial'
                            print 'Imprimiendo validar si existe'
                            print cobrarTarifa
                            self.ser = self.initSerialEsperandoOK()
                            errorCobro = self.parsearSaldoCobrar(tipoTisc, csn, cobrarTarifa, saldo, nuevoSaldo, lonSaldoNuevo, enListaNegra, int(folio), self.ser)
                            if enListaNegra == True or errorCobro == True:
                                self.closeSerial()
                                if enListaNegra == True:
                                    print 'No mando imagen porque esta en lista negra'
                                    return 'NO,NV,S*S,1'
                                if errorCobro == True:
                                    print 'No mando imagen'
                                    return 'NO,VAI,S*S,1'
                            else:
                                self.closeSerial()
                                return csn+","+tipoTisc+","+nombre+","+str(nuevoSaldo)

                    if data[0] == "1":
                        print 'No hago nada'
                        numError = 1
                        self.ser = self.initSerial()
                        self.algunError(numError, self.ser)
                        no = 'NO,VAI,S*S,1'
                        return no
                    if data[0] == "2":
                        print 'No hago nada'
                        numError = 1
                        self.ser = self.initSerial()
                        self.algunError(numError, self.ser)
                        no = 'NO,VAI,S*S,1'
                        return no
                    else:
                        numError = 1
                        self.ser = self.initSerial()
                        self.algunError(numError, self.ser)
                        no = 'NO,VAI,S*S,1'
                        return no
            print 'Sali del self. if datos'


        print 'Termine el proceso de pago'
        return True
        
    def cobrar_ant(self, datos, ser):
        print 'Empiezo el proceso de cobro'
        self.datos = datos
        self.ser = ser
        print "Datos: ",self.datos
        #print "Ser: ",self.ser
        if self.datos:
            for c in self.datos:
                if c == '\n':
                    data = list(datos)
                    print "Recibi el fin de linea..."
                    longLis = len(datos)
                    print 'Longitud de la cadena', longLis
                    if data[0] == "3":
                        '''
                            TODO
                            Validar que cuando haya error en algun punto
                            quitar el println y dejar puros print ya que
                            el buffer se queda con errores de validaciones
                            anteriores :)
                        '''
                        print 'Es EV2'
                        self.valoresCard = self.funcCore.validarDataEV2(data)
                        if self.valoresCard['error']:
                                numError = 1
                                self.ser = self.initSerial()
                                self.algunError(numError, self.ser)
                                no = 'NO,NV,S*S,1'
                                return no
                        else:
                            print 'Aca esta el valor csn del diccionario'
                            print self.valoresCard.get("csn")
                            print self.valoresCard.get("llave")
                            print self.valoresCard.get("nomTipoTar")
                            print self.valoresCard.get("eTarjeta")
                            print self.valoresCard.get("idTipoTarjeta")
                            print self.valoresCard.get("fecha")
                            print self.valoresCard.get("nombre")
                            print self.valoresCard.get("apellido")
                            print self.valoresCard.get("folio")
                            print self.valoresCard.get("saldo")
                            self.validacionLLlaveB = self.funcCore.validacionLlave\
                                (self.valoresCard.get('llave'),\
                                 self.valoresCard.get('csn'))
                            if self.validacionLLlaveB:
                                print 'Llave digital es invalida'
                                numError = 1
                                self.ser = self.initSerial()
                                self.algunError(numError, self.ser)
                                no = 'NO,NV,S*S,1'
                                return no
                            else:
                                if(self.valoresCard.get("nomTipoTar") == 'KI'):
                                    print 'Es un pinche chofi chofi'
                                    nombre = self.valoresCard.get("nombre") + " " + self.valoresCard.get("apellido")
                                    self.ser = self.initSerial()
                                    respuesta = self.inicioFinVueltaChofer(self.ser, self.valoresCard.get("csn"), nombre)
                                    #print 'Respuesta de abajo', respuesta
                                    numError = 4
                                    self.algunError(numError, self.ser)
                                    self.closeSerial()
                                    
                                    conn = sqlite3.connect(self.openDBAforo)
                                    c = conn.cursor()
                                    c.execute("SELECT nombre FROM configuraSistema, ruta WHERE idRutaActual = id")
                                    data = c.fetchone()
                                    c.close()
                                    if data is None:
                                        self.lblRuta.setText("")
                                    else:
                                        self.lblRuta.setText(data[0])
                                    conn.close
                                    
                                    no = '%s,O,S*S,%s,%s'%(self.valoresCard.get("csn"), str(respuesta), nombre)
                                    #no = 'NO,O,S*S,'
                                    return no
                                if(self.valoresCard.get("nomTipoTar") == 'AN'):
                                    self.ser = self.initSerial()
                                    respuesta = self.mostrarAforosOInicioFinTurno(self.ser, self.valoresCard.get("csn"))
                                    print 'Respuesta de abajo', respuesta
                                    numError = 4
                                    self.algunError(numError, self.ser)
                                    self.closeSerial()
                                    nombre = self.valoresCard.get("nombre") + " " + self.valoresCard.get("apellido")
                                    #no = 'NO,A%s,S*S,1'%str(respuesta)
                                    no = 'NO,A,S*S,%s,%s'%(str(respuesta), nombre)
                                    return no
                                else:
                                    print 'La firma digital es correcta'
                                    validarSiExiste = self.obtenerTarifa(\
                                        self.valoresCard.get('idTipoTarjeta'))
                                    print validarSiExiste
                                    if validarSiExiste == False:
                                        print 'Tarifa no existe en el sistema no \
                                            se puede cobrar'
                                        numError = 1
                                        self.ser = self.initSerial()
                                        self.algunError(numError, self.ser)
                                        no = 'NO,NV,S*S,1'
                                        return no
                                    else:
                                        print 'Tarifa valida en el sistema'
                                        cobrarTarifa = validarSiExiste
                                        self.validarSaldo = self.funcCore.saldoSuf(\
                                            cobrarTarifa, self.valoresCard.get\
                                            ('saldo'))
                                        if self.validarSaldo:
                                            print 'Iniciando el serial'
                                            self.ser = self.initSerial()
                                            self.sinSaldo(cobrarTarifa, \
                                            self.valoresCard.get\
                                            ('saldo'), self.ser)
                                            self.closeSerial()
                                            #DAACD9C7,ES,don**vergas*u8ov��,959
                                            no = 'NO,SS,S*S,%s'%str(self.valoresCard.get('saldo'))
                                            return no
                                        else:
                                            print 'Saldo suficiente cobrare'
                                            nuevoSaldo = int(self.valoresCard.get('saldo')) - int(validarSiExiste)
                                            print nuevoSaldo, " = ", int(self.valoresCard.get('saldo')), " - ", int(validarSiExiste)
                                            lonSaldoNuevo = len(str(nuevoSaldo))
                                            
                                            respuesta = self.funcCore.validarListaNegra(self.valoresCard.get("csn"))
                                            print 'Iniciando el Serial'
                                            print 'Imprimiendo validar si existe'
                                            print validarSiExiste
                                            self.ser = self.initSerialEsperandoOK()
                                            errorCobro = self.parsearSaldoCobrar  \
                                            (self.valoresCard.get("nomTipoTar"), self.valoresCard.get("csn"),\
                                            validarSiExiste, self.valoresCard.get("saldo"), nuevoSaldo,\
                                            lonSaldoNuevo, respuesta, int(self.valoresCard.get("folio")),self.ser)
                                            if respuesta == True or errorCobro == True:
                                                self.closeSerial()
                                                if respuesta == True:
                                                    print 'No mando imagen porque esta en lista negra'
                                                    no = 'NO,NV,S*S,1'
                                                    return no
                                                if errorCobro == True:
                                                    print 'No mando imagen'
                                                    no = 'NO,VAI,S*S,1'
                                                    return no
                                            else:
                                                self.closeSerial()
                                                respuesta = self.valoresCard.get("csn")+","+self.valoresCard.get("nomTipoTar")+\
                                                    ","+self.valoresCard.get("nombre")+","+str(nuevoSaldo)
                                                return respuesta
                    if data[0] == "1":
                        print 'No hago nada'
                        numError = 1
                        self.ser = self.initSerial()
                        self.algunError(numError, self.ser)
                        no = 'NO,VAI,S*S,1'
                        return no
                    if data[0] == "2":
                        print 'No hago nada'
                        numError = 1
                        self.ser = self.initSerial()
                        self.algunError(numError, self.ser)
                        no = 'NO,VAI,S*S,1'
                        return no
                    else:
                            numError = 1
                            self.ser = self.initSerial()
                            self.algunError(numError, self.ser)
                            no = 'NO,VAI,S*S,1'
                            return no
            print 'Sali del self. if datos'
        print 'Termine el proceso de pago'
        return True

    def inicioFinVueltaChofer(self, ser, csn, stOperador):
        self.ser = ser
        #funcion que inicia o termna un recorrido
        fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(self.openDBAforo)
        c = conn.cursor()
        #Validar si hay una vuelta iniciada o no
        c.execute("SELECT idUnidad, kmActual FROM configuraSistema");
        datosSistema = c.fetchone()
        c.close()
        if datosSistema is None:
            print('No existen datos de configuracion del sistema')
        else:
            print('Si existen los datos necesaios del sistema')
            idUni = datosSistema[0]
            kmAct = datosSistema[1]
        #voy a buscar si hay turno iniciado si no no inicio
        c = conn.cursor()  
        c.execute("SELECT inicioFin FROM turnoDelDia ORDER BY idTurnoDelDia DESC LIMIT 1")
        turno = c.fetchone()
        c.close()
        if turno[0] == 'I':
            #busco si la vuelt esta iniciada o terminada si esta iniciada me decuelte un I
            #por lo cual la voy a finzalizar
            # si me devuelve una F la voy a iniciar
            c = conn.cursor()
            c.execute("SELECT inicioFin FROM soloVuelta ORDER BY idSoloVuelta DESC LIMIT 1")
            data = c.fetchone()
            c.close()
            if data[0] == 'I':
                print 'Voy a finalizar'
                #self.lblTN.setText('Finalizando')
                #self.lblTNV.setText('vuelta')
                c = conn.cursor()
                c.execute("SELECT km, csn, num_vuelta FROM soloVuelta ORDER BY idSoloVuelta DESC LIMIT 1")
                data = c.fetchone()
                c.close()
                if data is None:
                    print 'No hay vueltas antes'
                else:
                    km = data[0]
                    csnA  = data[1]
                    nVuelta = data[2]
                c = conn.cursor()
                c.execute("SELECT idUnidad, idRutaActual FROM configuraSistema")
                ruta = c.fetchone()
                c.close()
                if ruta is None:
                    print 'No hay vueltas antes'
                else:
                    iUnidad = ruta[0]
                    ruta = ruta[1]
                c = conn.cursor()   
                c.execute("SELECT kmEstimado FROM ruta WHERE id = ?", (ruta, ))
                kmE = c.fetchone()
                c.close()
                if kmE is None:
                    print 'kmEstimado no se encuentra'
                else:
                    kmS = kmE[0]
                    
                kmNuevo = int(km) + int(kmS)
                c = conn.cursor()
                c.execute("SELECT turno FROM turnoDelDia ORDER BY idTurnoDelDia DESC LIMIT 1")
                turno = c.fetchone()
                c.close()
                if turno is None:
                    print 'No hay turnos'
                else:
                    turnoA = turno[0]
                #INSERT INTO soloVuelta(fechahora, km, idUnidad, csn, num_vuelta, turno, inicioFin, enviados) VALUES(?, ?, ?, ?, ?, ?,? ,?), ('esta-siempre-va', 0, 0, 00000000, 0, 'M','F', 1);
                conn.execute("INSERT INTO soloVuelta(fechahora, km, idUnidad, idRuta, csn, num_vuelta, turno, inicioFin, enviados) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (fechaHora, kmNuevo, iUnidad, ruta, csn, nVuelta, turnoA, 'F', 0))
                conn.commit()
                #actualizo el kilometraje de la unidad despues de la vuelta
                conn.execute("UPDATE configuraSistema SET kmActual = ?, operador = ''",(kmNuevo, ))
                conn.commit()
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
                c = conn.cursor()
                c.execute("SELECT km, csn, num_vuelta, fechahora FROM soloVuelta ORDER BY idSoloVuelta DESC LIMIT 1")
                data = c.fetchone()
                c.close()
                if data is None:
                    print 'No hay vueltas antes'
                else:
                    km = data[0]
                    csnA  = data[1]
                    nVuelta = data[2]
                    fecha = data[3]

                c = conn.cursor()
                c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                data = c.fetchone()
                c.close()
                if data is None:
                    print('No hay parametros de configuracon contacta al administrador')
                else:
                    idUni = data[0]
                    idRuta = data[1]

                c = conn.cursor()
                c.execute("SELECT turno FROM turnoDelDia ORDER BY idTurnoDelDia DESC LIMIT 1")
                turno = c.fetchone()
                c.close()
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
                    conn.execute("INSERT INTO soloVuelta(fechahora, km, idUnidad, idRuta, csn, num_vuelta, turno, inicioFin, enviados) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (fechaHora, kmAct, idUni, idRuta, csn, self.nVuelta, turnoA, 'I', 0))
                    conn.commit()
                else:
                    #nVueltaNueva = int(nVuelta) + 1
                    print 'Error en la validaciop'
                    conn.execute("INSERT INTO soloVuelta(fechahora, km, idUnidad, idRuta, csn, num_vuelta, turno, inicioFin, enviados) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (fechaHora, kmAct, idUni, idRuta, csn, 1, turnoA, 'I', 0))
                    conn.commit()

                conn.execute("UPDATE configuraSistema SET operador = ?",(stOperador, ))
                conn.commit()

                numError = 4
                return 2
                #self.algunError(numError, self.ser)

        if turno[0] == 'F':
            #self.lblTN.setText('No hay turno iniciado')
            print 'No hay turno inciado'
            numError = 4
            return 3
            #self.algunError(numError, self.ser)
        conn.close

    def mostrarAforosOInicioFinTurno(self, ser, csn):
            '''
                ##############################################################
                    Funcion que muestra aforos si hay una vuelta iniciada
                    o inicia o termina turno.
                ##############################################################
            '''
            respuesta = 0;
            self.ser = ser
            conn = sqlite3.connect(self.openDBAforo)

            #Consulta que me devuelve si hay o no un turno iniciado
            c = conn.cursor()
            c.execute("SELECT fechaHora, turno, inicioFin  FROM \
                turnoDelDia WHERE date('now')=date(fechaHora) ORDER BY \
                idTurnoDelDia DESC LIMIT 1")
            data = c.fetchone()
            c.close()
            if data is None:
                print 'No hay turno iniciado'
                #Valido si hay un paso de tarjeta anterior para ver si quiere cerrar el turno
                c = conn.cursor()
                c.execute("SELECT id, fechahora FROM inicioFinTurno")
                hayDato = c.fetchone()
                c.close()
                if hayDato is None:
                    print 'Es la primera la guardo'
                    tiempoActual = time.strftime("%H:%M:%S")
                    conn.execute("INSERT INTO inicioFinTurno(fechahora) VALUES(?)", (tiempoActual,))
                    conn.commit()
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
                        conn.execute("DELETE FROM inicioFinTurno WHERE id = ?", (idBorrar, ))
                        conn.commit()
                        print 'Registro Borrado'
                        c = conn.cursor()
                        c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                        data = c.fetchone()
                        c.close()
                        if data is None:
                            print('No hay parametros de configuracon contacta al administrador')
                        else:
                            idUni = data[0]
                            idRuta = data[1]
                        conn.execute("INSERT INTO turnoDelDia(fechahora, idUnidad, \
                        idRuta, csn, turno, inicioFin, enviados) \
                        VALUES(?, ?, ?, ?, ?, ?, ?)", (fechaHora, idUni, \
                        idRuta, csn, turnoLocal, inFin, 0))
                        conn.commit()
                        respuesta =  21
                    #esto pasa cuando ya hay un tiempo y es mas la diferencia
                    #entr tiempos asi que los voy a eliminar
                    else:
                        print 'Eliminando tiempos'
                        idBorrar = hayDato[0]
                        conn.execute("DELETE FROM inicioFinTurno WHERE id = ?", (idBorrar, ))
                        conn.commit()
                        print 'Registro Borrado'
                        respuesta = 11
            else:
                turno = data[1]
                print 'Si hay un turno iniciado'
                #Valido si hay un paso de tarjeta anterior para ver si quiere cerrar el turno
                c = conn.cursor()
                c.execute("SELECT id, fechahora FROM inicioFinTurno")
                hayDato = c.fetchone()
                c.close()
                if hayDato is None:
                    print 'Es la primera la guardo'
                    tiempoActual = time.strftime("%H:%M:%S")
                    conn.execute("INSERT INTO inicioFinTurno(fechahora) VALUES(?)", (tiempoActual,))
                    conn.commit()
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
                        conn.execute("DELETE FROM inicioFinTurno WHERE id = ?", (idBorrar, ))
                        conn.commit()
                        print 'Registro Borrado'
                        #lo que voy a hacer aca es que si el turno anterior es un
                        #inicio solo lo voy a finalizar tal cual
                        if data[2] == 'I':
                            c = conn.cursor()
                            c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                            data = c.fetchone()
                            c.close()
                            if data is None:
                                print('No hay parametros de configuracon contacta al administrador')
                            else:
                                idUni = data[0]
                                idRuta = data[1]

                            conn.execute("INSERT INTO turnoDelDia(fechahora, idUnidad, \
                            idRuta, csn, turno, inicioFin, enviados) \
                            VALUES(?, ?, ?, ?, ?, ?, ?)", (fechaHora, idUni, \
                            idRuta, csn, turno, inFin, 0))
                            conn.commit()
                            respuesta = 3;
                        else:
                        #if data[2] == 'F':
                            turnoNuevo = int(turno) + 1
                            c = conn.cursor()
                            c.execute("SELECT idTurno from tTurno WHERE idTurno = ?", (turnoNuevo,))
                            turnoN = c.fetchone()
                            c.close()
                            if turnoN is None:
                                print 'No hay turno siguiente'

                                turnoLocal = 1
                                inFin = "I"
                                fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")
                                c = conn.cursor()
                                c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                                data = c.fetchone()
                                c.close()
                                if data is None:
                                    print('No hay parametros de configuracon contacta al administrador')
                                else:
                                    idUni = data[0]
                                    idRuta = data[1]

                                conn.execute("INSERT INTO turnoDelDia(fechahora, idUnidad, \
                                idRuta, csn, turno, inicioFin, enviados) \
                                VALUES(?, ?, ?, ?, ?, ?, ?)", (fechaHora, idUni, \
                                idRuta, csn, turnoLocal, inFin, 0))
                                conn.commit()
                                respuesta = 21
                            else:
                                print 'Si hay un turno siguiente'
                                inFin = "I"
                                fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")
                                c = conn.cursor()
                                c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                                data = c.fetchone()
                                c.close()
                                if data is None:
                                    print('No hay parametros de configuracon contacta al administrador')
                                else:
                                    idUni = data[0]
                                    idRuta = data[1]

                                conn.execute("INSERT INTO turnoDelDia(fechahora, idUnidad, \
                                idRuta, csn, turno, inicioFin, enviados) \
                                VALUES(?, ?, ?, ?, ?, ?, ?)", (fechaHora, idUni, \
                                idRuta, csn, turnoNuevo, inFin, 0))
                                conn.commit()
                                respuesta= 21
                    #no supero el tiempo asi que no lo voy a acabar
                    else:
                        print 'Eliminando tiempos'
                        idBorrar = hayDato[0]
                        conn.execute("DELETE FROM inicioFinTurno WHERE id = ?", (idBorrar, ))
                        conn.commit()
                        print 'Registro Borrado'
                        respuesta = 11

            numError = 4
            conn.close
            return respuesta
            #self.algunError(numError, self.ser)

    def algunError(self, numError, ser):
        self.ser = ser
        #este se tiene que enviar para que el cobrador no se
        #quede esperando el posible nuevo saldo
        mensajes = ['Hiram Zuniga','Tarjeta invalida en el sistema', \
            'Ya habias pagado','Tarjeta invalida',' ', '','Tarifa no actualizada']
        print 'Enviando codigo de cancelacion de transaccion'
        #time.sleep(self.retardo)
        self.ser.write('9999999')
        aforoExitoso = 1
        while(aforoExitoso == 1):
            exito = ser.readline()
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
                        #self.msg.setText(mensajes[numError])
                    else:
                        print 'No se hizo la transacion aviar al usuario del aforo normal'
                        aforoExitoso = 2
                        print 'Suelto el hanger'

    def sinSaldo(self, tarifaC, saldoPesos ,ser):
        '''
        print 'No tiene saldo suficiente para tarifa actual a cobrar'
        ser.write('11111')
        aforoExitoso = 1
        while(aforoExitoso == 1):
            exito = ser.readline()
            print('Esperando el NO')
            esperaRespuesta = 0
            esperaRespuesta = esperaRespuesta + 1
            for c in exito:
                if c == '':
                    print 'Que me regresa el validador'
                    rExito = list(exito)
                    print(rExito)
                    if(rExito[0] == 'N' and rExito[1] == 'O'):
                        print 'Recibi el NO por serial'
                        print 'No hago nada solo ceere bien la transaccion'
                        #Variable para romper el while
                        aforoExitoso = 2
                    else:
                        print 'No se hizo la transacion aviar al usuario del aforo normal'
                        aforoExitoso = 2
                        print 'Suelto el hanger'
        '''

        print 'No tiene saldo suficiente para tarifa actual a cobrar'
        ser.write('9999999')
        #self.guardarAforo(tipoS, csnS, nuevoSaldo, tarifaC)
        aforoExitoso = 1
        esperaRespuesta = 0
        while aforoExitoso == 1:
            print 'Esperando el NO'
            #ser.flushInput()
            #ser.flushOutput()
            time.sleep(0.1)
            exito = ser.readline()
            esperaRespuesta = esperaRespuesta + 1
            print esperaRespuesta
            #print 'No recibi nada'
            if esperaRespuesta == 2:
                aforoExitoso = 1
                break
            #for c in exito:
            my_list = exito.split(",")
            print 'aca imprimo lo que tiene exito', my_list
            if my_list[0] == 'NO\r\n':
                print 'Que me regresa el validador?', exito
                rExito = list(exito)
                #print rExito
                if(rExito[0] == 'N' and rExito[1] == 'O'):
                    print 'Recibi el NO por serial'
                    print 'No hago nada solo ceere bien la transaccion'
                    #Variable para romper el while
                    #aforoExitoso = 2
                    return True
                else:
                    print 'No se hizo la transacion aviar al usuario del aforo normal'
                    print 'Suelto el hanger'
                    #aforoExitoso = 2
                    return True
            else:
                print 'No se hizo la transacion aviar al usuario del aforo normal'
                print 'Suelto el hanger'
                #aforoExitoso = 2
                return True


    def parsearSaldoCobrar(self, tipoS, csnS, tarifaC, saldoPesos,nuevoSaldo, lonSaldoNuevo, respuesta, folio, ser):
        if respuesta == False:
            if lonSaldoNuevo == 1:
                print 'Saldo con 1 caracteres rellenar para que sean 5 '
                nuevoSaldoCompleto = '000000' + str(nuevoSaldo)
                ser.write(str(nuevoSaldoCompleto))
            if lonSaldoNuevo == 2:
                print 'Saldo con 2 caracteres rellenar para que sean 5 '
                nuevoSaldoCompleto = '00000' + str(nuevoSaldo)
                ser.write(str(nuevoSaldoCompleto))
            if lonSaldoNuevo == 3:
                print 'Saldo con 3 caracteres rellenar para que sean 5 '
                nuevoSaldoCompleto = '0000' + str(nuevoSaldo)
                ser.write(str(nuevoSaldoCompleto))
            if lonSaldoNuevo == 4:
                print 'Saldo con 4 caracteres rellenar para que sean 5 '
                nuevoSaldoCompleto = '000' + str(nuevoSaldo)
                print nuevoSaldoCompleto
                ser.write(str(nuevoSaldoCompleto))
            if lonSaldoNuevo == 5:
                print 'Saldo con 5 no voy a rellenar'
                nuevoSaldoCompleto = '00' + str(nuevoSaldo)
                ser.write(str(nuevoSaldoCompleto))
            if lonSaldoNuevo == 6:
                print 'Saldo con 5 no voy a rellenar'
                nuevoSaldoCompleto = '0' + str(nuevoSaldo)
                ser.write(str(nuevoSaldoCompleto))
            if lonSaldoNuevo == 7:
                print 'Saldo con 5 no voy a rellenar'
                nuevoSaldoCompleto = str(nuevoSaldo)
                ser.write(str(nuevoSaldoCompleto))

            print "Nuevo Saldo: ", nuevoSaldoCompleto

            #self.guardarAforo(tipoS, csnS, nuevoSaldo, tarifaC)
            aforoExitoso = 1
            esperaRespuesta = 0
            while aforoExitoso == 1:
                print 'Esperando el OK'
                #ser.flushInput()
                #ser.flushOutput()
                time.sleep(0.1)
                exito = ser.readline()
                esperaRespuesta = esperaRespuesta + 1
                print esperaRespuesta
                #print 'No recibi nada'
                if esperaRespuesta == 2:
                    aforoExitoso = 1
                    break
                #for c in exito:
                my_list = exito.split(",")
                print 'aca imprimo lo que tiene exito', my_list
                if my_list[0] == 'OK\r\n':
                    print 'Que me regresa el validador?', exito
                    rExito = list(exito)
                    #print rExito
                    if(rExito[0] == 'O' and rExito[1] == 'K'):
                        print 'Recibi el OK, guardando aforo'
                        #print 'Entonces si voy a guaradr'
                        self.guardarAforo(tipoS, csnS, nuevoSaldo, tarifaC, folio)
                        #aforoExitoso = 2
                        return False
                    else:
                        print 'No se hizo la transacion aviar al usuario del \
                            aforo normal'
                        print 'Suelto el hanger'
                        #aforoExitoso = 2
                        return True
                else:
                    print 'No se hizo la transacion aviar al usuario del aforo \
                        normal'
                    print 'Suelto el hanger'
                    #aforoExitoso = 2
                    return True
        else:
            print 'La csn esta reportada con anomalias Esta en la lista negra y no puedo cobrar'
            #ser.write('11111')
            ser.write('9999999')
            aforoExitoso = 1
            while(aforoExitoso == 1):
                exito = ser.readline()
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
                            #Variable para romper el while
                            aforoExitoso = 2
                            return True
                        else:
                            print 'No se hizo la transacion aviar al usuario \
                                del aforo normal'
                            aforoExitoso = 2
                            print 'Suelto el hanger'
                            return True


    def parsearSaldoCobrarEV2(self, tipoS, csnS, tarifaC, saldoPesos,nuevoSaldo, lonSaldoNuevo, respuesta, ser, saldo):
        if respuesta == False:
            ser.write('11111')
            #self.guardarAforo(tipoS, csnS, nuevoSaldo, tarifaC)
            aforoExitoso = 1
            esperaRespuesta = 0
            while aforoExitoso == 1:
                print 'Esperando el OK'
                #ser.flushInput()
                #ser.flushOutput()
                time.sleep(0.1)
                exito = ser.readline()
                esperaRespuesta = esperaRespuesta + 1
                print esperaRespuesta
                #print 'No recibi nada'
                if esperaRespuesta == 2:
                    aforoExitoso = 1
                    break
                #for c in exito:
                my_list = exito.split(",")
                print 'aca imprimo lo que tiene exito', my_list
                if my_list[0] == 'OK\r\n':
                    print 'Que me regresa el validador?', exito
                    rExito = list(exito)
                    #print rExito
                    if(rExito[0] == 'O' and rExito[1] == 'K'):
                        print 'Recibi el OK, guardando aforo'
                        #print 'Entonces si voy a guaradr'
                        print 'Mientras no lo voy a guardar'
                        #print tipoS
                        #print csnS
                        #print nuevoSaldo
                        #print tarifaC
                        self.actualizarSaldoEV2(csnS, tarifaC, saldo)
                        self.guardarAforo(tipoS, csnS, nuevoSaldo, tarifaC)
                        #aforoExitoso = 2
                        return False
                    else:
                        print 'No se hizo la transacion aviar al usuario del \
                            aforo normal'
                        print 'Suelto el hanger'
                        #aforoExitoso = 2
                        return True
                else:
                    print 'No se hizo la transacion aviar al usuario del aforo \
                        normal'
                    print 'Suelto el hanger'
                    #aforoExitoso = 2
                    return True
        else:
            print 'La csn esta reportada con anomalias Esta en la lista negra y no puedo cobrar'
            ser.write('9999999')
            aforoExitoso = 1
            while(aforoExitoso == 1):
                exito = ser.readline()
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
                            #Variable para romper el while
                            aforoExitoso = 2
                            return True
                        else:
                            print 'No se hizo la transacion aviar al usuario \
                                del aforo normal'
                            aforoExitoso = 2
                            print 'Suelto el hanger'
                            return True


    def actualizarSaldoEV2(self, csn, tarifa, saldo):
        saldonuevo = int(saldo) - int(tarifa)
        self.Scsn = str(csn)
        conn = sqlite3.connect(self.openDBEV2)
        #c = conn.cursor()
        conn.execute("UPDATE tag SET saldo = ? WHERE csn = ?",(saldonuevo, self.Scsn, ))
        conn.commit()
        conn.close


    def yaPagoAntes(self, tipoS, csnS):
        print 'Validando si ya pago antes'
        enviados = 0
        ini = 'I'
        conn = sqlite3.connect(self.openDBAforo)
        c = conn.cursor()
        c.execute("SELECT fechaHora FROM soloVuelta WHERE inicioFin=? ORDER BY idSoloVuelta DESC LIMIT 1", (ini,))
        comparar = c.fetchone()
        c.close()
        if comparar is None:
            print 'No hay turno activo el dia de hoy'
        else:
            horaComparar = comparar[0]
        c = conn.cursor()
        c.execute("SELECT fechaHora FROM validador WHERE csn = ? ORDER BY idValidador DESC LIMIT 1" ,(csnS, ))
        data = c.fetchone()
        c.close()
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
        conn.close
        if tdelta == True:
            #return True
            return False
        else:
            return False

    def obtenerTarifa(self, tipoTS):
        print 'Obteniendo tarifa actual'
        try:
            conn = sqlite3.connect(self.cdDb)
            c = conn.cursor()
            c.execute("SELECT cantidad FROM tar WHERE nom = ?", (str(tipoTS),))
            tarifa = c.fetchone()
            c.close()
            conn.close
            if tarifa is None:
                print 'No se encuentra la tarifa para este tipo de usuario'
                return False
            else:
                tarifaC = tarifa[0]
                return tarifaC
        except:
            return False

    def guardarAforo(self, tipoS, csnS, nuevoSaldo, tarifaC, folio):
        enviados = 0
        print 'Guardando aforo...'
        #Obtener los datos a utilizar constantes en este caso
        #dos idUnidad y idChofer

        '''
            Ahora solo agregare el folio primero le sumare una accion y despues
            lo guardare
        '''
        print 'Dentro de parsearCobrar aca esta el folio que guardare pero primero le sumare uno'
        print folio
        print type(folio)
        folio += 1
        print folio

        conn = sqlite3.connect(self.openDBAforo)
        c = conn.cursor()
        c.execute('SELECT idUnidad FROM configuraSistema')
        data = c.fetchone()
        c.close()
        if data is None:
            print('No hay parametros de configuracon contacta al administrador')
        else:
            idUni = data[0]

        c = conn.cursor()
        c.execute('SELECT idChofer FROM usuario')
        dataUsuario = c.fetchone()
        c.close()
        if dataUsuario is None:
            print('No hay parametros de configuracon contacta al administrador')
        else:
            idChofer = dataUsuario[0]

        fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")
        #c = conn.cursor()
        conn.execute("INSERT INTO validador(idTipoTisc, idUnidad, idOperador, csn, saldo, tarifa, fechaHora, folios, enviado) values(?, ?, ?, ?, ?, ?, ?, ?, ?)", (tipoS, idUni, idChofer, csnS, nuevoSaldo, tarifaC, fechaHora, str(folio), enviados))
        conn.commit()
        conn.close



