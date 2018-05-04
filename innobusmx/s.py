#!/usr/bin/python
# -*- coding: utf-8 -*-

import serial
import os


velocidad = 115200
sPort = ""
sPort3G = ""     
idCons = 0


def inicializaGPS():
    print '###             Iniciando GPS             ###'
    cmd = "AT+QGPS=1\r"
    ser.write(cmd.encode())
    stRead = ""
    while (stRead[-2:] != "OK") and not ((stRead[-3:] >= "501") and (stRead[-3:] <= "549")):
        stRead += str(ser.read(1))
    print "QGPS: "+stRead

    if (stRead[-2:] == "OK"):
        print '###       El GPS OK                       ###'
    else:
        if (stRead[-3:] == "504"):
            print '###       El GPS ya esta encendido        ###'
        else:
            print '###       Hay un problema con el GPS      ###'
            print '###       GPS: '+stRead


def obtenerCoordenadaGPS(idCons):
    cmd = 'AT+QGPSLOC=0\r'
    try:
        i = ser.write(cmd.encode())
        stRead = ""
        while (stRead[-2:] != "OK") and not ((stRead[-10:] >= "ERROR: 501") and (stRead[-10:] <= "ERROR: 549")) and (stRead[-18:] != '+QIURC: "closed",0') and (stRead != "Reset"):
            ch = ser.read(1)
            if (str(ch) == "None"):
                stRead = "Reset"
            else:
                stRead += str(ch)
#            stRead += str(ser.read(1))
    except:
        stRead = "Reset"
        
    print "QGPSLOC: "+stRead
    if(stRead[-2:] == "OK"):
        try:
            stRead = " ".join(stRead.split()) #se le aplica un split al mismo comando
            my_list = stRead.split(",")
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
            datetimes = fecha + ' ' + hora
            gpr = '1,1,1,,'+str(datetimes)+','+str(latitud)+','+str(longitud)+','+str(velGPS)+','+str(idCons)+'\r'+''
            print "GPS " + gpr
        except:
            print '###   GPS fallo el parseo del dato   ###'
    else:
        if (stRead[-18:] != '+QIURC: "closed",0'):
            print '###   Error Conexion con el Servidor     ###'                
        else:
            velGPS = 0

    if (stRead == "Reset"):
        inicializaGPS()
    
    
def initUSB():
    sPort = ""
    while (sPort == ''):
        path = "/dev"
        listdir = os.listdir(path)
        for file in listdir:
            if (file[0:6] == "ttyUSB"):
                s = serial.Serial("/dev/"+file, velocidad, timeout=1, writeTimeout=1)
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
                    sPort = "/dev/"+file
                if (st == "AT"):
                    sPort3G = "/dev/"+file
                            
    print "RFID: "+sPort
    print "3G:"+sPort3G



idCons = 0
sPort = ""
sPort3G = ""
initUSB()
print "sPort3G:",sPort3G
ser = serial.Serial(sPort3G, velocidad, timeout=1)

print '###           Reiniciando MODEM          ###'
cmd = 'AT+QRST=1,0\r'
ser.write(cmd.encode())
stRead = ""
while (stRead[-3:] != "RDY"):
    stRead += str(ser.read(1))
print "AT+QRST: " +stRead

inicializaGPS()
while (True):
    idCons = idCons + 1
    obtenerCoordenadaGPS(idCons)



    
print "Fin"

