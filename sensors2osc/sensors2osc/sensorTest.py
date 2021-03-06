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

import argparse
import os.path
import select
import serial
import socket
import sys
import datetime

try:
    from chaosc.c_osc_lib import OSCMessage
except ImportError as e:
    print(e)
    from chaosc.osc_lib import OSCMessage


class Forwarder(object):
    def __init__(self, actor, platform, device):
        self.actor = actor
        self.platform = platform
        self.device = device
        self.serial = serial.Serial()
        self.serial.port = device
        self.serial.baudrate = 115200
        self.serial.timeout = 0
        self.buf_ser2osc = ""

        self.serial.open()

    def close(self):
        """Close all resources and unpublish service"""
        print "%s: closing..." % (self.device, )
        self.serial.close()


class EHealth2OSC(Forwarder):
    def __init__(self, actor, platform, device):
        super(EHealth2OSC, self).__init__(actor, platform, device)

    def handle_read(self, osc_sock):
        data = self.serial.readline()[:-2]
        print repr(data)
        try:
            airFlow, emg, temp = data.split(";")
        except ValueError:
            return
        try:
            airFlow = int(airFlow)
            emg = int(emg)
            temp = int(temp);
        except ValueError:
            return
        osc_message = OSCMessage("/%s/airFlow" % self.actor)
        osc_message.appendTypedArg(airFlow, "i")
        osc_sock.sendall(osc_message.encode_osc())
        osc_message = OSCMessage("/%s/emg" % self.actor)
        osc_message.appendTypedArg(emg, "i")
        osc_sock.sendall(osc_message.encode_osc())
        osc_message = OSCMessage("/%s/temperature" % self.actor)
        osc_message.appendTypedArg(temp, "i")
        osc_sock.sendall(osc_message.encode_osc())


class EKG2OSC(Forwarder):
    def __init__(self, actor, platform, device):
        super(EKG2OSC, self).__init__(actor, platform, device)

    def handle_read(self, osc_sock):
        t = ord(self.serial.read(1))
        osc_message = OSCMessage("/%s/ekg" % self.actor)
        osc_message.appendTypedArg(t, "i")
        osc_sock.sendall(osc_message.encode_osc())


class RingBuffer(object):
    def __init__(self, length):
        self.length = length
        self.ring_buf = [-1 for i in xrange(length)]
        self.head = 0

    def append(self, value):
        self.ring_buf[self.head] = value
        self.head = (self.head + 1) % self.length

    def getData(self):
        print "getData", self.ring_buf, self.head
        data = list()
        for i in range(7, 1, -1):
            value = self.ring_buf[(self.head - i) % self.length]
            if value == -1:
                raise ValueError("not complete")
            data.append(value)
        if data[0] != 0x0 or data[1] != 0xff:
            raise ValueError("not synced")
        return data[2:]



class Pulse2OSC(Forwarder):
    def __init__(self, actor, platform, device):
        super(Pulse2OSC, self).__init__(actor, platform, device)
        self.buf = RingBuffer(6)
        self.heartbeat_on = False

    def handle_read(self, osc_sock):
        t = ord(self.serial.read(1))
        self.buf.append(t)

        if t == 0:
            try:
                heart_signal, heart_rate, o2, pulse = self.buf.getData()

                if pulse == 245 and not self.heartbeat_on:
                    osc_message = OSCMessage("/%s/heartbeat" % self.actor)
                    osc_message.appendTypedArg(1, "i")
                    osc_message.appendTypedArg(heart_rate, "i")
                    osc_message.appendTypedArg(o2, "i")
                    osc_sock.sendall(osc_message.encode_osc())
                    print "heartbeat", datetime.datetime.now(), heart_signal
                    self.heartbeat_on = True
                elif pulse == 1 and self.heartbeat_on:
                    #print "off heartbeat", datetime.datetime.now(), heart_signal
                    self.heartbeat_on = False
                    osc_message = OSCMessage("/%s/heartbeat" % self.actor)
                    osc_message.appendTypedArg(0, "i")
                    osc_message.appendTypedArg(heart_rate, "i")
                    osc_message.appendTypedArg(o2, "i")
                    osc_sock.sendall(osc_message.encode_osc())
            except ValueError, e:
                print e


def main():
    parser = argparse.ArgumentParser(prog='psychose_actor')
    parser.add_argument("-H", '--chaosc_host', required=True,
        type=str, help='host of chaosc instance to control')
    parser.add_argument("-p", '--chaosc_port', required=True,
        type=int, help='port of chaosc instance to control')
    parser.add_argument("-t", '--type', required=True,
        type=str, help='ekg, pulse, ehealth')
    parser.add_argument("-d", '--device', required=True,
        type=str, help='device node under /dev')
    parser.add_argument("-a", '--actor', required=True,
        type=str, help='actor name')


    args = parser.parse_args(sys.argv[1:])

    osc_sock = socket.socket(2, 2, 17)
    osc_sock.connect((args.chaosc_host, args.chaosc_port))

    used_devices = dict()

    actor = args.actor
    if args.type == "ehealth":
        used_devices[device] = EHealth2OSC(actor, "ehealth", args.device)
    elif args.type == "ekg":
        used_devices[device] = EKG2OSC(actor, "ekg", args.device)
    elif args.type == "pulse":
        used_devices[device] = Pulse2OSC(actor, "pulse", args.device)
    else:
        raise ValueError("unknown description %r for device %r" % (description, device))

    while 1:
        read_map = {}
        for forwarder in used_devices.values():
            read_map[forwarder.serial] = forwarder.handle_read

        readers, writers, errors = select.select(read_map, [], [], 0.1)
        for reader in readers:
            read_map[reader](osc_sock)
