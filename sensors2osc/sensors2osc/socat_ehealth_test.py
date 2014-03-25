#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of sensors2osc package
#
# sensors2osc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# sensors2osc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with sensors2osc.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2014 Stefan Kögl

# used this line before opening that script
# socat -d -d PTY,raw,echo=0,link=/tmp/pty1,b115200,user=stefan PTY,raw,echo=0,link=/tmp/pty2,b115200,user=stefan

import serial, sys, time, random, struct

serial_sock = serial.Serial()
serial_sock.port = sys.argv[1]
serial_sock.baudrate = 115200
serial_sock.timeout = 0
serial_sock.open()


while 1:
    serial_sock.write("%d;%d;%d\r\n" % (random.randint(0,1023), random.randint(0,1023), random.randint(0,1023)))
    time.sleep(0.05)
