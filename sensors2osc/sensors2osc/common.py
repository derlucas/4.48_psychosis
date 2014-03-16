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


class Platform(object):
    def __init__(self, args):
        self.args = args
        self.serial_sock = None
        self.osc_sock = socket.socket(2, 2, 17)
        self.osc_sock.connect((self.args.chaosc_host, self.args.chaosc_port))


    def connect(self):
        print "connect serial"
        self.serial_sock = serial.Serial()
        self.serial_sock.port = self.args.device
        self.serial_sock.baudrate = 115200
        self.serial_sock.timeout = 0
        self.serial_sock.open()


    def close(self):
        if self.serial_sock is not None:
            print "close serial"
            self.serial_sock.close()


    def reconnect(self):
        print "reconnect serial"
        self.close()
        self.connect()


def create_args(name):
    arg_parser = create_arg_parser(name)
    main_group = arg_parser.add_argument_group("main")
    main_group.add_argument("-d", '--device', required=True,
        type=str, help='device node under /dev')
    main_group.add_argument("-a", '--actor', required=True,
        type=str, help='actor name')
    add_chaosc_group(arg_parser)

    args = finalize_arg_parser(arg_parser)
    return args


def init(name):
    args = create_args(name)
    platform = Platform(args)
    platform.connect()
    atexit.register(platform.close)

    return platform
