#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import ConfigParser
import os.path
import random
import re
import select
import serial
import socket
import sys
import time
import struct
import datetime


try:
    from chaosc.c_osc_lib import *
except ImportError as e:
    print(e)
    from chaosc.osc_lib import *


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

        #try:
        self.serial.open()
        #self.serial.setRTS(False)
        self.alive = True
        #except Exception, e:
            #print "opening", e
            #self.serial.close()

    def close(self):
        """Close all resources and unpublish service"""
        print "%s: closing..." % (self.device, )
        self.alive = False
        self.serial.close()


class EHealth2OSC(Forwarder):
    def __init__(self, actor, platform, device):
        super(EHealth2OSC, self).__init__(actor, platform, device)

    def handleRead(self, osc_sock):
        pass


class EKG2OSC(Forwarder):
    def __init__(self, actor, platform, device):
        super(EKG2OSC, self).__init__(actor, platform, device)

    def handleRead(self, osc_sock):
        t = ord(self.serial.read(1))
        osc_message = OSCMessage("/%s/ekg" % self.actor)
        osc_message.appendTypedArg(t, "i")
        osc_sock.sendall(osc_message.encode_osc())



class Pulse2OSC(Forwarder):
    def __init__(self, actor, platform, device):
        super(Pulse2OSC, self).__init__(actor, platform, device)
        self.buf = [0 for i in xrange(24)]
        self.position = 0
        self.start = -1
        self.heartbeat_send = False

    def handleRead(self, osc_sock):
        t = ord(self.serial.read(1))
        pos = (self.position + 1) % 24
        self.buf[pos] = t
        self.position = pos
        if t == 0:
            self.start = pos

        #print "start", self.start
        if self.start > -1:
            data = range(6)
            for i in range(6):
                data[i] = self.buf[(self.start + i) % 24]

            sync1, sync2, heart_signal, heart_rate, o2, pulse = data

            #print sync1, sync2, heart_signal, heart_rate, o2, pulse
            if pulse == 245 and not self.heartbeat_send:
                osc_message = OSCMessage("/%s/heartbeat" % self.actor)
                osc_message.appendTypedArg(1, "i")
                osc_message.appendTypedArg(heart_rate, "i")
                osc_message.appendTypedArg(o2, "i")
                osc_sock.sendall(osc_message.encode_osc())
                print "heartbeat", datetime.datetime.now(), heart_signal
                self.heartbeat_send = True
            elif pulse == 1 and self.heartbeat_send:
                #print "off heartbeat", datetime.datetime.now(), heart_signal
                self.heartbeat_send = False
                osc_message = OSCMessage("/%s/heartbeat" % self.actor)
                osc_message.appendTypedArg(0, "i")
                osc_message.appendTypedArg(heart_rate, "i")
                osc_message.appendTypedArg(o2, "i")
                osc_sock.sendall(osc_message.encode_osc())

            #osc_message = OSCMessage("/%s/o2" % self.actor)
            #osc_message.appendTypedArg(o2, "i")
            #osc_sock.sendall(osc_message.encode_osc())

            #osc_message = OSCMessage("/%s/heartrate" % self.actor)
            #osc_message.appendTypedArg(heart_rate, "i")
            #osc_sock.sendall(osc_message.encode_osc())
            self.start = -1




def main():
    parser = argparse.ArgumentParser(prog='psychose_actor')
    parser.add_argument("-H", '--chaosc_host', required=True,
        type=str, help='host of chaosc instance to control')
    parser.add_argument("-p", '--chaosc_port', required=True,
        type=int, help='port of chaosc instance to control')


    args = parser.parse_args(sys.argv[1:])

    connections = list()
    osc_sock = socket.socket(2, 2, 17)
    osc_sock.connect((args.chaosc_host, args.chaosc_port))


    naming = {
        "/dev/ttyUSB0" : ["merle", "ehealth"],
        "/dev/ttyUSB1" : ["merle", "ekg"],
        "/dev/ttyUSB2" : ["merle", "pulse"],
        "/dev/ttyUSB3" : ["bjoern", "ehealth"],
        "/dev/ttyUSB4" : ["bjoern", "ekg"],
        "/dev/ttyUSB5" : ["bjoern", "pulse"],
        "/dev/ttyUSB6" : ["uwe", "ehealth"],
        "/dev/ttyUSB7" : ["uwe", "ekg"],
        "/dev/ttyUSB8" : ["uwe", "pulse"]
        }

    naming = {
        "/dev/ttyACM0" : ["merle", "pulse"],
        #"/dev/ttyACM1" : ["merle", "pulse"]
        }

    used_devices = dict()

    while 1:
        for device, description in naming.iteritems():
            if os.path.exists(device):
                if device not in used_devices:
                    actor, platform = naming[device]
                    if description[1] == "ehealth":
                        print device, actor, platform
                        used_devices[device] = EHealth2OSC(actor, platform, device)
                    elif description[1] == "ekg":
                        print device, actor, platform
                        used_devices[device] = EKG2OSC(actor, platform, device)
                    elif description[1] == "pulse":
                        print device, actor, platform
                        used_devices[device] = Pulse2OSC(actor, platform, device)
                    else:
                        raise ValueError("unknown description %r for device %r" % (description, device))
            else:
                print "device missing", device
                m = OSCMessage("/DeviceMissing")
                m.appendTypedArg(description[0], "s")
                m.appendTypedArg(description[1], "s")
                osc_sock.sendall(m.encode_osc())

        read_map = {}
        for forwarder in used_devices.values():
            read_map[forwarder.serial] = forwarder.handleRead

        readers, writers, errors = select.select(read_map, [], [], 0.1)
        #print "readers", readers
        for reader in readers:
            read_map[reader](osc_sock)
