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

import time

from sensors2osc.common import *



def main():
    platform = init("ekg2osc")

    actor = platform.args.actor

    while 1:
        try:
            t = platform.serial_sock.read(1)
        except socket.error, msg:
            # got disconnected?
            print "serial socket error!!!", msg
            platform.reconnect()

        try:
            t = ord(t)
        except TypeError, e:
            continue

        try:
            print "got value", t
            osc_message = OSCMessage("/%s/ekg" % actor)
            osc_message.appendTypedArg(t, "i")
            platform.osc_sock.sendall(osc_message.encode_osc())
        except socket.error, msg:
            print "cannot connect to chaosc"
            continue


if __name__ == '__main__':
    main()
