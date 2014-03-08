#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import re
import sys
import httplib

from chaosc.simpleOSCServer import SimpleOSCServer


class OSC2CamServer(SimpleOSCServer):
    """OSC filtering/transcoding middleware
    """

    def __init__(self, args, cams):
        """ctor for a osc udp 2 ptz ip cam bridge

        starts the server, creates http connections to specified cams

        :param args: return value of argparse.parse_args
        :type args: namespace object

        :param cams: return value of argparse.parse_args
        :type cams: list of 2 item tuples
        """

        SimpleOSCServer.__init__(self, ("", args.port))

        self.set_url = "/cgi-bin/admin/"
        self.get_url = "/cgi-bin/view/"
        self.ptz_ctl_url = "/cgi-bin/operator/ptzset"
        self.ptz_config_url = "/cgi-bin/operator/ptzconfig"
        self.connections = [httplib.HTTPConnection(host, port) for host, port in cams]
        self.resetCams()

    def resetCams(self):
        """ configures each ip cam"""

        for connection in self.connections:
            connection.request("GET", "%sparam?action=update&Image.I0.MJPEG.Resolution=640x480" % self.set_url)
            conn_result = connection.getresponse()
            print conn_result.status, conn_result.reason
            connection.request("GET", "%sparam?action=update&Image.I0.Appearance.Compression=75" % self.set_url)
            conn_result = connection.getresponse()
            print conn_result.status, conn_result.reason
            connection.request("GET", "%sparam?action=update&Image.I0.MJPEG.FPS=25" % self.set_url)
            conn_result = connection.getresponse()
            print conn_result.status, conn_result.reason


    def move_cam(self, cam_id, args):
        """ moves given ip cam"""

        direction = args[0]
        if direction in ("home", "up", "down", "left", "right", "upleft", "upright", "downleft", "downright", "repeat", "stop"):
            connection = self.connections[cam_id]
            connection.request("GET", "%s?move=%s" % (self.ptz_ctl_url, direction))
            conn_result = connection.getresponse()
            print conn_result.status, conn_result.reason


    def use_cam_preset(self, cam_id, args):
        """ says given ip cam to use a predefined position preset"""

        presetno = args[0]
        connection = self.connections[cam_id]
        connection.request("GET", "%s?gotoserverpresetno=%d" % (self.ptz_ctl_url, presetno))
        conn_result = connection.getresponse()
        print conn_result.status, conn_result.reason


    def set_cam_preset(self, cam_id, args):
        """ saves the actual position of given ip cam to a preset"""

        presetno = args[0]
        connection = self.connections[cam_id]
        connection.request("GET", "%s?setserverpresetno=%d&home=yes" % (self.ptz_config_url, presetno))
        conn_result = connection.getresponse()
        print conn_result.status, conn_result.reason


    def zoom_cam(self, cam_id, args):
        """ tells given ip cam to zoom in or out"""

        direction = None
        arg = args[0]
        if arg == "out":
            direction = 0
        elif arg == "in":
            direction = 1
        connection = self.connections[cam_id]
        connection.request("GET", "%s?zoom=%s" % (self.ptz_ctl_url, direction))
        conn_result = connection.getresponse()
        print conn_result.status, conn_result.reason


    def toggle_night_view(self, cam_id, args):
        """ toggles the night view function of given ip cam"""

        arg = args[0]
        state = None
        if arg == "on":
            state = "auto"
        else:
            state = "off"

        connection = self.connections[cam_id]
        connection.request("GET", "%sparam?action=update&Image.I0.Appearance.NightMode=%s" % (self.set_url, state))
        conn_result = connection.getresponse()
        print conn_result.status, conn_result.reason


    def dispatchMessage(self, osc_address, typetags, args, packet, client_address):
        """ dispatches parsed osc messages to the ip cam command methods"""
        rule = re.compile("^/(.*?)/(\d+)/(.*?)$")
        res = rule.match(osc_address)
        if res:
            _, cam_id, command = res.groups()
            cam_id = int(cam_id)
            if command == "moveCam":
                self.move_cam(cam_id, args)
            elif command == "setCamPreset":
                self.set_cam_preset(cam_id, args)
            elif command == "useCamPreset":
                self.use_cam_preset(cam_id, args)
            elif command == "zoomCam":
                self.zoom_cam(cam_id, args)
            elif command == "toggleNightView":
                self.toggle_night_view(cam_id, args)


def main():
    parser = argparse.ArgumentParser(prog='osc2cam')
    parser.add_argument('-p', "--port", required=True,
        type=int, help='my port')

    args = parser.parse_args(sys.argv[1:])


    cams = [
        ("192.168.1.51", args.port + 1),
        ("192.168.1.52", args.port + 2),
        ("192.168.1.53", args.port + 3),
    ]

    cams = [
        ("localhost", args.port + 1),
        ("localhost", args.port + 2),
        ("localhost", args.port + 3),
    ]


    server = OSC2CamServer(args, cams)
    server.serve_forever()

