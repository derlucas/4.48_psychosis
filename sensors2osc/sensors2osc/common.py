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
import time
import sys

from chaosc.argparser_groups import ArgParser


try:
    from chaosc.c_osc_lib import OSCMessage
except ImportError as e:
    print(e)
    from chaosc.osc_lib import OSCMessage


class Platform(object):
    def __init__(self, args):
        self.args = args
        self.remote = (self.args.chaosc_host, self.args.chaosc_port)
        self.serial_sock = None
        self.osc_sock = socket.socket(args.address_family, 2, 17)
        self.osc_sock.connect((self.args.chaosc_host, self.args.chaosc_port))


    def connect(self):
        print "connect serial"
        print "waiting for the device %r to come up" % self.args.device
        self.serial_sock = serial.Serial()
        self.serial_sock.port = self.args.device
        self.serial_sock.baudrate = 115200
        self.serial_sock.timeout = 1
        while 1:
            try:
                self.serial_sock.open()
            except (serial.serialutil.SerialException, os.error), e:
                print "serial error", e
                time.sleep(0.5)
                pass
            else:
                break


    def close(self):
        if self.serial_sock is not None:
            print "close serial"
            self.serial_sock.close()


    def reconnect(self):
        print "reconnect serial"
        self.close()
        self.connect()


def create_args(name):
    arg_parser = ArgParser(name)
    arg_parser.add_global_group()
    main_group = arg_parser.add_argument_group("main")
    arg_parser.add_argument(main_group, "-D", '--device',
        help='device node under /dev')
    arg_parser.add_argument(main_group, "-a", '--actor',
        help='actor name')
    arg_parser.add_argument(main_group, '-b', '--baudrate', type=int, default=115200, choices=sorted(serial.baudrate_constants.keys()),
        help='selects the baudrate, default=115200, for valid values execute "import serial;print sorted(serial.baudrate_constants.keys())"')
    arg_parser.add_chaosc_group()

    args = arg_parser.finalize()
    return args


def init():
    args = create_args(os.path.basename(sys.argv[0]))
    platform = Platform(args)
    platform.connect()
    atexit.register(platform.close)

    return platform
