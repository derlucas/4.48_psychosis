#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of chaosc
#
# chaosc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# chaosc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with chaosc.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2014 Stefan Kögl

import socket, argparse, sys


try:
    from chaosc.c_osc_lib import OSCMessage, decode_osc
except ImportError, e:
    print e
    from chaosc.osc_lib import OSCMessage, decode_osc


def send(sock, binary, args):
    sent = sock.sendto(binary, (args.osc2cam_host, args.osc2cam_port))
    response = sock.recv(4096)
    if response:
        osc_address, typetags, arguments = decode_osc(response, 0, len(response))
        print osc_address, arguments


def test_move_cam(args, cam_id, sock):
    directions = ("home", "up", "down", "left", "right", "upleft", "upright", "downleft", "downright")
    for direction in directions:
        message = OSCMessage("/moveCam")
        message.appendTypedArg(cam_id, "i")
        message.appendTypedArg(direction, "s")
        binary = message.encode_osc()
        send(sock, binary, args)


def test_use_cam_preset(args, cam_id, sock):
    for i in range(10):
        message = OSCMessage("/useCamPreset")
        message.appendTypedArg(cam_id, "i")
        message.appendTypedArg(i, "i")
        binary = message.encode_osc()
        send(sock, binary, args)


def test_set_cam_preset(args, cam_id, sock):
    message = OSCMessage("/setCamPreset")
    message.appendTypedArg(cam_id, "i")
    message.appendTypedArg(0, "i")
    binary = message.encode_osc()
    send(sock, binary, args)


def test_zoom_cam(args, cam_id, sock):
    for i in (1, 5000, 9999):
        message = OSCMessage("/zoomCam")
        message.appendTypedArg(cam_id, "i")
        message.appendTypedArg(i, "i")
        binary = message.encode_osc()
        send(sock, binary, args)


def test_focus_cam(args, cam_id, sock):
    for i in (1, 5000, 9999):
        message = OSCMessage("/focusCam")
        message.appendTypedArg(cam_id, "i")
        message.appendTypedArg(i, "i")
        binary = message.encode_osc()
        send(sock, binary, args)


def test_toggle_night_view(args, cam_id, sock):
    for i in ("on", "off"):
        message = OSCMessage("/toggleNightView")
        message.appendTypedArg(cam_id, "i")
        message.appendTypedArg(i, "s")
        binary = message.encode_osc()
        send(sock, binary, args)



def parse_cam_config(path):
    lines = open(path).readlines()
    cams = list()
    for line in lines:
        host, port = line.split(",")
        host = host.strip()
        port = int(port.strip())
        cams.append((host, port))
    return cams



def main():
    parser = argparse.ArgumentParser(prog='osc2cam-test')
    parser.add_argument("-o", '--osc2cam_host', required=True,
        type=str, help='host of osc2cam instance to control')
    parser.add_argument("-p", '--osc2cam_port', required=True,
        type=int, help='port of osc2cam instance to control')
    parser.add_argument('-c', "--cam-config-file", required=True,
            type=str, help='txt file for cam configuration, each line should be of the form "host, port"')

    args = parser.parse_args(sys.argv[1:])

    cams = parse_cam_config(args.cam_config_file)

    sock = socket.socket(2, 2, 17)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
    sock.settimeout(1)
    sock.bind(("localhost", 10000))
    #sock.connect((args.osc2cam_host, args.osc2cam_port))

    for ix, (host, port) in enumerate(cams):
        test_move_cam(args, ix, sock)
        test_use_cam_preset(args, ix, sock)
        test_set_cam_preset(args, ix, sock)
        test_zoom_cam(args, ix, sock)
        test_focus_cam(args, ix, sock)
        test_toggle_night_view(args, ix, sock)

main()
