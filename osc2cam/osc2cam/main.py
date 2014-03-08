#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import re
import sys
import httplib

from datetime import datetime
from chaosc.simpleOSCServer import SimpleOSCServer

try:
    from chaosc.c_osc_lib import OSCMessage
except ImportError, e:
    print e
    from chaosc.osc_lib import OSCMessage


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

        self.args = args
        self.set_url = "/cgi-bin/admin/"
        self.get_url = "/cgi-bin/view/"
        self.ptz_ctl_url = "/cgi-bin/operator/ptzset"
        self.ptz_config_url = "/cgi-bin/operator/ptzconfig"
        self.parse_cam_config()
        self.connections = [httplib.HTTPConnection(host, port) for host, port in cams]
        self.resetCams()
        self.targets = list()


    def parse_cam_config(self):
        lines = open(self.args.cam_config_file).readlines()
        cams = list()
        for line in lines:
            host, port = line.split(",")
            host = host.strip()
            port = int(port.strip())
            cams.append((host, port))
        return cams


    def handleConnResult(self, connection, *args, **kwargs):
        conn_result = connection.getresponse()
        if "client_address" in kwargs:
            response = OSCMessage("/Response")
            response.appendTypedArg(kwargs["cmd"], "s")
            for arg in args:
                response.append(arg)
            response.appendTypedArg(conn_result.status, "i")
            response.appendTypedArg(conn_result.reason, "s")
            self.socket.sendto(response.encode_osc(), kwargs["client_address"])

        if conn_result.status != 200:
            print "%s. Error: %d, %s" % (datetime.now().strftime("%x %X"), conn_result.status, conn_result.reason)



    def resetCams(self):
        """ configures each ip cam"""

        now = datetime.now().strftime("%x %X")
        for ix, connection in enumerate(self.connections):
            print "%s: resetting camera %d to: resolution 640x480, 75%% compression and 25 fps" % (now, ix)
            connection.request("GET", "%sparam?action=update&Image.I0.MJPEG.Resolution=640x480" % self.set_url)
            self.handleConnResult(connection, None)
            connection.request("GET", "%sparam?action=update&Image.I0.Appearance.Compression=75" % self.set_url)
            self.handleConnResult(connection, None)
            connection.request("GET", "%sparam?action=update&Image.I0.MJPEG.FPS=25" % self.set_url)
            self.handleConnResult(connection, None)


    def move_cam(self, cam_id, args, client_address):
        """ moves given ip cam"""

        direction = args[0]
        now = datetime.now().strftime("%x %X")
        if direction in ("home", "up", "down", "left", "right", "upleft", "upright", "downleft", "downright"):
            print "%s: move camera %d to: dir %r" % (now, cam_id, direction)
            connection = self.connections[cam_id]
            url = "%s?move=%s" % (self.ptz_ctl_url, direction)
            try:
                repeat = args[1] == "repeat"
                url += "?move=repeat"
            except IndexError:
                pass
            connection.request("GET", url)
            self.handleConnResult(connection, *args, client_address=client_address, cmd="moveCam")



    def use_cam_preset(self, cam_id, args, client_address):
        """ says given ip cam to use a predefined position preset"""

        presetno = args[0]
        connection = self.connections[cam_id]
        now = datetime.now().strftime("%x %X")
        print "%s: use camera %d preset %d" % (now, cam_id, presetno)

        connection.request("GET", "%s?gotoserverpresetno=%d" % (self.ptz_ctl_url, presetno))
        self.handleConnResult(connection, *args, client_address=client_address, cmd="useCamPreset")


    def set_cam_preset(self, cam_id, args, client_address):
        """ saves the actual position of given ip cam to a preset"""

        presetno = args[0]
        connection = self.connections[cam_id]
        connection.request("GET", "%s?setserverpresetno=%d" % (self.ptz_config_url, presetno))
        self.handleConnResult(connection, *args, client_address=client_address, cmd="setCamPreset")


    def zoom_cam(self, cam_id, args, client_address):
        """ tells given ip cam to zoom in or out"""

        step = args[0]
        now = datetime.now().strftime("%x %X")
        print "%s: zoom camera %d to position %d" % (now, cam_id, step)

        connection = self.connections[cam_id]
        connection.request("GET", "%s?zoom=%d" % (self.ptz_ctl_url, step))
        self.handleConnResult(connection, *args, client_address=client_address, cmd="zoomCam")


    def focus_cam(self, cam_id, args, client_address):
        """ tells given ip cam to zoom in or out"""

        step = args[0]
        now = datetime.now().strftime("%x %X")
        print "%s: focus camera %d to position %d" % (now, cam_id, step)

        connection = self.connections[cam_id]
        connection.request("GET", "%s?focus=%d" % (self.ptz_ctl_url, step))
        self.handleConnResult(connection, *args, client_address=client_address, cmd="focusCam")


    def toggle_night_view(self, cam_id, args, client_address):
        """ toggles the night view function of given ip cam"""

        arg = args[0]
        state = None
        if arg == "on":
            state = "auto"
        else:
            state = "off"

        connection = self.connections[cam_id]
        connection.request("GET", "%sparam?action=update&Image.I0.Appearance.NightMode=%s" % (self.set_url, state))
        self.handleConnResult(connection, *args, client_address=client_address, cmd="toggleNightView")

    def stop_cam(self, cam_id, args, client_address):
        """stops cam movement"""

        now = datetime.now().strftime("%x %X")
        print "%s: stop camera %d" % (now, cam_id)
        connection = self.connections[cam_id]
        connection.request("GET", "%s?move=stop" % (self.ptz_ctl_url))
        self.handleConnResult(connection, *args, client_address=client_address, cmd="stopCam")


    def dispatchMessage(self, osc_address, typetags, args, packet, client_address):
        """ dispatches parsed osc messages to the ip cam command methods"""

        cam_id = args.pop(0)
        if osc_address == "/moveCam":
            self.move_cam(cam_id, args, client_address)
        elif osc_address == "/setCamPreset":
            self.set_cam_preset(cam_id, args, client_address)
        elif osc_address == "/useCamPreset":
            self.use_cam_preset(cam_id, args, client_address)
        elif osc_address == "/zoomCam":
            self.zoom_cam(cam_id, args, client_address)
        elif osc_address == "/focusCam":
            self.zoom_cam(cam_id, args, client_address)
        elif osc_address == "/stopCam":
            self.zoom_cam(cam_id, args, client_address)
        elif osc_address == "/toggleNightView":
            self.toggle_night_view(cam_id, args, client_address)
        elif osc_address == "/subscribe":
            self.__subscription_handler(osc_address, typetags, args, packet, client_address)


    def __subscription_handler(self, addr, typetags, args, client_address):
        """handles a target subscription.

        The provided 'typetags' equals ["s", "i"] and
        'args' contains [host, portnumber]

        only subscription requests with valid host will be granted.
        """

        address = args
        try:
            r = socket.getaddrinfo(address[0], address[1], socket.AF_INET6, socket.SOCK_DGRAM, 0, socket.AI_V4MAPPED | socket.AI_ALL)
            print "addrinfo", r
            if len(r) == 2:
                address = r[1][4]
            try:
                print "%s: subscribe %r (%s:%d) by %s:%d" % (
                    datetime.now().strftime("%x %X"), args[3], address[0],
                    address[1], client_address[0], client_address[1])
                self.targets[tuple(address)] =  args[3]
            except IndexError:
                self.targets[tuple(address)] =  ""
                print "%s: subscribe (%s:%d) by %s:%d" % (
                    datetime.now().strftime("%x %X"), address[0], address[1],
                    client_address[0], client_address[1])
        except socket.error, error:
            print error
            print "subscription attempt from %r: host %r not usable" % (
                client_address, address[0])



def main():
    parser = argparse.ArgumentParser(prog='osc2cam')
    parser.add_argument('-p', "--port", required=True,
        type=int, help='my port')
    parser.add_argument('-C', "--client_port", required=True,
        type=int, help='client port to send reponse to')
    parser.add_argument('-c', "--cam-config-file", required=True,
        type=str, help='txt file for cam configuration, each line should be of the form "host, port"')

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

