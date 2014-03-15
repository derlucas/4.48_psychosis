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

import atexit
import os.path
import serial
import socket

from chaosc.argparser_groups import *

try:
    from chaosc.c_osc_lib import OSCMessage
except ImportError as e:
    print(e)
    from chaosc.osc_lib import OSCMessage

serial_sock = None

def connect(args):
    print "connect serial"
    global serial_sock
    serial_sock = serial.Serial()
    serial_sock.port = args.device
    serial_sock.baudrate = 115200
    serial_sock.timeout = 0


def close():
    global serial
    if serial_sock is not None:
        print "close serial"
        serial_sock.close()


def reconnect(args):
    print "reconnect serial"
    global serial_sock
    close()
    connect(args)


def create_args(name):
    arg_parser = create_arg_parser(name)
    main_group = arg_parser.add_argument_group("main")
    main_group.add_argument("-d", '--device', required=True,
        type=str, help='device node under /dev')
    main_group.add_argument("-a", '--actor', required=True,
        type=str, help='actor name')
    add_chaosc_group(arg_parser)

    args = finalize_arg_parser(arg_parser)


    while 1:
        try:
            t = ord(serial_sock.read(1))
            print "got value", t
            osc_message = OSCMessage("/%s/ekg" % actor)
            osc_message.appendTypedArg(t, "i")
            osc_sock.sendall(osc_message.encode_osc())
        except socket.error, msg:
            # got disconnected?
            print "lost connection!!!"
            reconnect(args)

def init(name):
    args = create_args(name)
    osc_sock = socket.socket(2, 2, 17)
    osc_sock.connect((args.chaosc_host, args.chaosc_port))

    connect(args)
    return args, osc_sock

