#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import commands

a=commands.getoutput ('sudo find /home/pi/innobusmx -name "*.hex"')

print a

os.system('avrdude -v -patmega328p -Uflash:w:'+a+':i -carduino -b 115200 -P /dev/ttyUSB1')
