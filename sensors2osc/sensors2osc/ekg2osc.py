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

from sensors2osc import common

atexit.register(close)

def main():
    args, osc_sock = init("ekg2osc")

    actor = args.actor

    while 1:
        try:
            t = ord(common.serial_sock.read(1))
            print "got value", t
            osc_message = OSCMessage("/%s/ekg" % actor)
            osc_message.appendTypedArg(t, "i")
            osc_sock.sendall(osc_message.encode_osc())
        except socket.error, msg:
            # got disconnected?
            print "lost connection!!!"
            reconnect(args)



if __name__ == '__main__':
    main()
