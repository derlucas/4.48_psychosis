# -*- coding: utf-8 -*-

# This file is part of chaosc
#
# chaosc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# chaosc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with chaosc.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2014 Stefan Kögl

# used this line before opening that script
# socat -d -d PTY,raw,echo=0,link=/tmp/pty1,b115200,user=stefan PTY,raw,echo=0,link=/tmp/pty2,b115200,user=stefan


from __future__ import absolute_import

import serial, time, random, sys, random, struct


serial_sock = serial.Serial()
serial_sock.port = sys.argv[1]
serial_sock.baudrate = 115200
serial_sock.timeout = 0
serial_sock.open()


class DataGenenerator(object):
    def  __init__(self):
        self.get_i = 0

    def read(self):
        value = None
        if self.get_i == 0:
            value = random.randint(1, 254)
        elif self.get_i == 1:
            value = random.sample((1, 245), 1)[0]
        elif self.get_i == 2:
            value = 0
        elif self.get_i == 3:
            value = 255
        elif self.get_i == 4:
            value = random.randint(1, 255)
        elif self.get_i == 5:
            value = random.randint(1, 255)

        self.get_i = (self.get_i + 1) % 6
        return value

r = DataGenenerator()

while 1:
    serial_sock.write(struct.pack("B", r.read()))
    #time.sleep(0.1)
