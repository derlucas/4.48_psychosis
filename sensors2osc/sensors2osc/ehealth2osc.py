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

from __future__ import absolute_import

from sensors2osc.common import *
import time, select


def main():
    platform = init("ehealth2osc")

    actor = platform.args.actor

    while 1:
        try:
            toread, towrite, toerrors = select.select([platform.serial_sock], [],[], 0.05)
            if toread:
                data = platform.serial_sock.readline()[:-2]
            else:
                continue
            #print repr(data)
        except socket.error, msg:
            # got disconnected?
            print "serial socket error!!!", msg
            platform.reconnect()

        print "got data", repr(data)
        try:
            airFlow, emg, temp = data.split(";")
        except ValueError, e:
            print e
            continue

        try:
            airFlow = int(airFlow)
        except ValueError, e:
            print e
            continue

        try:
            osc_message = OSCMessage("/%s/airFlow" % actor)
            osc_message.appendTypedArg(airFlow, "i")
            platform.osc_sock.sendall(osc_message.encode_osc())
        except socket.error, msg:
            print "cannot connect to chaosc", msg
            continue


        try:
            emg = int(emg)
        except ValueError, e:
            print e
            continue

        try:
            osc_message = OSCMessage("/%s/emg" % actor)
            osc_message.appendTypedArg(emg, "i")
            platform.osc_sock.sendall(osc_message.encode_osc())
        except socket.error, msg:
            print "cannot connect to chaosc", msg
            continue


        try:
            temp = int(temp)
        except ValueError, e:
            print e
            continue

        try:
            osc_message = OSCMessage("/%s/temperatur" % actor)
            osc_message.appendTypedArg(temp, "i")
            platform.osc_sock.sendall(osc_message.encode_osc())
        except socket.error, msg:
            print "cannot connect to chaosc", msg
            continue


if __name__ == '__main__':
    main()
