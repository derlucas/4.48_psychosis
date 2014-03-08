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

from chaosc.simpleOSCServer import SimpleOSCServer


try:
    from chaosc.c_osc_lib import *
except ImportError as e:
    print(e)
    from chaosc.osc_lib import *


class OSC2CamServer(SimpleOSCServer):
    """OSC filtering/transcoding middleware
    """

    def __init__(self, args, cams):
        """ctor for filter server

        starts the server, loads scene filters and transcoders and chooses
        the request handler, which is one of
        forward only, forward and dump, dump only.

        :param result: return value of argparse.parse_args
        :type result: namespace object
        """

        d = datetime.now().strftime("%x %X")
        print "%s: starting up chaosc_filter-%s..." % (d, chaosc._version.__version__)
        print "%s: binding to %s:%r" % (d, "0.0.0.0", args.own_port)
        SimpleOSCServer.__init__(self, ("0.0.0.0", args.own_port))

        self.set_url = "http://<servername>/cgi-bin/admin/"
        self.get_url = "http://<servername>/cgi-bin/view/"
        self.ptz_ctl_url = "http://myserver/cgi-bin/operator/ptzset"
        self.ptz_config_url = "http://myserver/cgi-bin/operator/ptzconfig"
        self.connections = [socket.create_connection(cam) for cam in cams]
        self.resetCams()

    def resetCams(self):
        for connection in self.connections:
            connection.sendall("%sparam?action=update&Image.I0.MJPEG.Resolution=640x480" % self.set_url)
            connection.sendall("%sparam?action=update&Image.I0.Appearance.Compression=75" % self.set_url)
            connection.sendall("%sparam?action=update&Image.I0.MJPEG.FPS=25" % self.set_url)


    def moveCam(self, cam_id, args):
        direction = args[0]
        if direction in ("home", "up", "down", "left", "right", "upleft", "upright", "downleft", "downright", "repeat", "stop"):
            self.connections[cam_id].sendall("%s?move=%s" % (self.ptz_ctl_url, direction))


    def useCamPreset(self, cam_id, args):
        presetno = args[0]
        self.connections[cam_id].sendall("%s?gotoserverpresetno=%d" % (self.ptz_ctl_url, presetno))


    def setCamPreset(self, cam_id, args):
        presetno = args[0]
        self.connections[cam_id].sendall("%s?setserverpresetno=%d&home=yes" % (self.ptz_config_url, presetno))


    def zoomCam(self, cam_id, args):
        direction = None
        arg = args[0]
        if arg == "out":
            direction = 0
        elif arg == "in":
            direction = 1
        self.connections[cam_id].sendall("%s?%szoom=%s" % (self.ptz_ctl_url, direction))


    def toggleNightView(self, cam_id, args):
        arg = args[0]
        state = None
        if arg == "on":
            state = "auto"
        else:
            state = "off"
        connection.sendall("%sparam?action=update&Image.I0.Appearance.NightMode=%s" % (self.set_url, state))


    def dispatchMessage(self, osc_address, typetags, args, packet, client_address):
        m = re.compile("/(.*?)/(\d+)/(.*?)")
        res = m.match(osc_address)
        if res:
            dust, cam_id, command
            if command == "moveCam":
                self.moveCam(cam_id, args)
            elif osc_address == "/setCamPreset":
                self.setCamPreset(cam_id, args)
            elif osc_address == "/useCamPreset":
                self.useCamPreset(cam_id, args)
            elif osc_address == "zoomCam":
                self.zoomCam(cam_id, args)
            elif osc_address == "toggleNightView":
                self.toggleNightView(cam_id, args)


def main():
    parser = argparse.ArgumentParser(prog='psychose_actor')
    parser.add_argument('-o', "--own_host", required=True,
        type=str, help='my host')
    parser.add_argument('-r', "--own_port", required=True,
        type=int, help='my port')

    args = parser.parse_args(sys.argv[1:])


    cams = [
        "192.168.1.51",
        "192.168.1.52",
        "192.168.1.53"
    ]

    server = OSC2CamServer(args, cams)
