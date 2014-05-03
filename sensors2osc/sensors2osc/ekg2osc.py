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

import time, select, sys

from sensors2osc.common import *
from chaosc.lib import logger


def main():
    platform = init()

    actor = platform.args.actor

    msg_count = 0

    while 1:
        try:
            toread, towrite, toerrors = select.select([platform.serial_sock], [],[], 0.01)
            if toread:
                t = platform.serial_sock.read(1)
            else:
                continue
        except (socket.error, serial.serialutil.SerialException), msg:
            # got disconnected?
            logger.exception(msg)
            logger.info("serial socket error!!! - try to reconnect")
            platform.reconnect()

        try:
            t = ord(t)
        except TypeError, e:
            continue

        if msg_count >= 20:
            logger.info("value = %d", t)
            msg_count = 0
        else:
            msg_count += 1

        try:
            osc_message = OSCMessage("/%s/ekg" % actor)
            osc_message.appendTypedArg(t, "i")
            platform.osc_sock.sendto(osc_message.encode_osc(), platform.remote)
        except socket.error, msg:
            logger.info("ekg2osc error")
            logger.exception(msg)
            continue


if __name__ == '__main__':
    main()
