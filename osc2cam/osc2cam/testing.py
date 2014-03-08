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
# Copyright (C) 2012-2013 Stefan Kögl


import socket, argparse, sys

from chaosc.simpleOSCServer import SimpleOSCServer


try:
    from chaosc.c_osc_lib import OSCMessage, decode_osc
except ImportError, e:
    print e
    from chaosc.osc_lib import OSCMessage, decode_osc




def test_moveCam(args, cam_id, sock):
    directions = ("home", "up", "down", "left", "right", "upleft", "upright", "downleft", "downright", "repeat", "stop")
    for direction in directions:
        moveCam = OSCMessage("/moveCam")
        moveCam.appendTypedArg(cam_id, "i")
        moveCam.appendTypedArg(direction, "s")
        binary = moveCam.encode_osc()

        try:
            sent = sock.sendto(binary, (args.osc2cam_host, args.osc2cam_port))
        except socket.error, e:
            if e[0] in (7, 65):     # 7 = 'no address associated with nodename',  65 = 'no route to host'
                raise e
            else:
                raise Exception("while sending OSCMessage 'moveCam' for cam_id %r with direction %r to %r:%r: %s" % (cam_id, direction, args.osc2cam_host, args.osc2cam_port, str(e)))
        response = sock.recv(4096)
        if response:
            osc_address, typetags, arguments = decode_osc(response, 0, len(response))
            print osc_address, arguments



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
        test_moveCam(args, ix, sock)

main()
