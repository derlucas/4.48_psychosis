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

import time, select
from datetime import datetime

from sensors2osc.common import *


class RingBuffer(object):
    def __init__(self, length):
        self.length = length
        self.ring_buf = list()
        self.reset()

    def reset(self):
        self.ring_buf = [-1] * self.length
        self.head = 0

    def append(self, value):
        self.ring_buf[self.head] = value
        self.head = (self.head + 1) % self.length

    def getData(self):
        print "getData", self.ring_buf, self.head
        data = list()
        for i in range(self.length + 1, 1, -1):
            value = self.ring_buf[(self.head - i) % self.length]
            if value == -1:
                self.reset()
                self.ring_buf[0] = 0
                self.head = 1
                raise ValueError("not complete - ringbuffer resettet")
            data.append(value)
        if data[0] != 0x0 or data[1] != 0xff:
            print "issue", data
            self.reset()
            self.ring_buf[0] = 0
            self.head = 1
            raise ValueError("not synced - ringbuffer resettet")
        return data[2:]


def main():
    platform = init("pulse2osc")

    actor = platform.args.actor

    buf = RingBuffer(6)
    heartbeat_on = False

    while 1:
        try:
            toread, towrite, toerrors = select.select([platform.serial_sock], [],[], 0.05)
            if toread:
                t = platform.serial_sock.read(1)
            else:
                continue
        except (socket.error, serial.serialutil.SerialException), msg:
            # got disconnected?
            print "serial socket error!!!", msg
            platform.reconnect()

        try:
            t = ord(t)
        except TypeError, e:
            continue

        print "got value", t
        buf.append(t)

        if t == 0:
            try:
                heart_signal, heart_rate, o2, pulse = buf.getData()
            except ValueError, e:
                print e
                continue

            if pulse == 245 and not heartbeat_on:
                heartbeat_on = True
                try:
                    osc_message = OSCMessage("/%s/heartbeat" % actor)
                    osc_message.appendTypedArg(1, "i")
                    osc_message.appendTypedArg(heart_rate, "i")
                    osc_message.appendTypedArg(o2, "i")
                    platform.osc_sock.sendall(osc_message.encode_osc())
                    print "on heartbeat", datetime.now(), heart_signal, heart_rate, o2, pulse
                except socket.error, msg:
                    print "cannot connect to chaosc"
                    continue
            elif pulse == 1 and heartbeat_on:
                print "off heartbeat", datetime.now(), heart_signal, heart_rate, o2, pulse
                heartbeat_on = False
                try:
                    osc_message = OSCMessage("/%s/heartbeat" % actor)
                    osc_message.appendTypedArg(0, "i")
                    osc_message.appendTypedArg(heart_rate, "i")
                    osc_message.appendTypedArg(o2, "i")
                    platform.osc_sock.sendall(osc_message.encode_osc())
                except socket.error, msg:
                    print "cannot connect to chaosc"
                    continue
        time.sleep(0.1)


if __name__ == '__main__':
    main()
