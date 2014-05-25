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
import time, select, sys


def main():
    platform = init()

    actor = platform.args.actor

    while 1:
        try:
            toread, towrite, toerrors = select.select([platform.serial_sock], [],[], 0.05)
            if toread:
                data = platform.serial_sock.readline()[:-2]
            else:
                continue
            #print repr(data)
        except (socket.error, serial.serialutil.SerialException), msg:
            # got disconnected?
            logger.exception(msg)
            platform.reconnect()

        try:
            airFlow, emg, temp = data.split(";")
        except ValueError, msg:
            logger.exception(msg)
            continue

        try:
            airFlow = int(airFlow)
        except ValueError, msg:
            logger.exception(msg)
            continue

        try:
            osc_message = OSCMessage("/%s/airFlow" % actor)
            osc_message.appendTypedArg(airFlow, "i")
            platform.osc_sock.sendto(osc_message.encode_osc(), platform.remote)
        except socket.error, msg:
            logger.exception(msg)
            continue


        try:
            emg = int(emg)
        except ValueError, msg:
            logger.exception(msg)
            continue

        try:
            osc_message = OSCMessage("/%s/emg" % actor)
            osc_message.appendTypedArg(emg, "i")
            platform.osc_sock.sendto(osc_message.encode_osc(), platform.remote)
        except socket.error, msg:
            logger.exception(msg)
            continue


        try:
            temp = int(temp)
        except ValueError, msg:
            logger.exception(msg)
            continue

        try:
            osc_message = OSCMessage("/%s/temperatur" % actor)
            osc_message.appendTypedArg(temp, "i")
            platform.osc_sock.sendto(osc_message.encode_osc(), platform.remote)
        except socket.error, msg:
            logger.exception(msg)
            continue


if __name__ == '__main__':
    main()
