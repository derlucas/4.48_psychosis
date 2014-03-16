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
# found the mjpeg part here, thanks for the nice code :)
# http://hardsoftlucid.wordpress.com/2013/04/11/mjpeg-server-for-webcam-in-python-with-opencv/
# the osc integration stuff is implemented by me
#
# Copyright (C) 2014 Stefan Kögl

from __future__ import absolute_import

from  datetime import datetime
import threading
import Queue
import numpy as np
import string,cgi,time, random, socket
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn, ForkingMixIn
import select
import re

from collections import deque

from PyQt4.QtCore import QBuffer, QByteArray, QIODevice
from PyQt4 import QtGui
import pyqtgraph as pg

from pyqtgraph.widgets.PlotWidget import PlotWidget

from chaosc.argparser_groups import *

try:
    from chaosc.c_osc_lib import *
except ImportError:
    from chaosc.osc_lib import *

QtGui.QApplication.setGraphicsSystem('opengl')


try:
    from chaosc.c_osc_lib import decode_osc
except ImportError as e:
    print(e)
    from chaosc.osc_lib import decode_osc

QAPP = QtGui.QApplication([])


class PlotWindow(PlotWidget):
    def __init__(self, title=None, **kargs):
        self.win = QtGui.QMainWindow()
        PlotWidget.__init__(self, **kargs)
        self.win.setCentralWidget(self)
        for m in ['resize']:
            setattr(self, m, getattr(self.win, m))
        if title is not None:
            self.win.setWindowTitle(title)


class OSCThread(threading.Thread):
    def __init__(self, args):
        super(OSCThread, self).__init__()
        self.args = args
        self.running = True
        self.own_address = socket.getaddrinfo(args.own_host, args.own_port, socket.AF_INET6, socket.SOCK_DGRAM, 0, socket.AI_V4MAPPED | socket.AI_ALL | socket.AI_CANONNAME)[-1][4][:2]

        self.chaosc_address = chaosc_host, chaosc_port = socket.getaddrinfo(args.chaosc_host, args.chaosc_port, socket.AF_INET6, socket.SOCK_DGRAM, 0, socket.AI_V4MAPPED | socket.AI_ALL | socket.AI_CANONNAME)[-1][4][:2]

        self.osc_sock = socket.socket(2, 2, 17)
        self.osc_sock.bind(self.own_address)
        self.osc_sock.setblocking(0)

        print "%s: starting up osc receiver on '%s:%d'" % (
            datetime.now().strftime("%x %X"), self.own_address[0], self.own_address[1])

        self.subscribe_me()

    def subscribe_me(self):
        """Use this procedure for a quick'n dirty subscription to your chaosc instance.

        :param chaosc_address: (chaosc_host, chaosc_port)
        :type chaosc_address: tuple

        :param receiver_address: (host, port)
        :type receiver_address: tuple

        :param token: token to get authorized for subscription
        :type token: str
        """
        print "%s: subscribing to '%s:%d' with label %r" % (datetime.now().strftime("%x %X"), self.chaosc_address[0], self.chaosc_address[1], self.args.subscriber_label)
        msg = OSCMessage("/subscribe")
        msg.appendTypedArg(self.own_address[0], "s")
        msg.appendTypedArg(self.own_address[1], "i")
        msg.appendTypedArg(self.args.authenticate, "s")
        if self.args.subscriber_label is not None:
            msg.appendTypedArg(self.args.subscriber_label, "s")
        self.osc_sock.sendto(msg.encode_osc(), self.chaosc_address)


    def unsubscribe_me(self):
        if self.args.keep_subscribed:
            return

        print "%s: unsubscribing from '%s:%d'" % (datetime.now().strftime("%x %X"), self.chaosc_address[0], self.chaosc_address[1])
        msg = OSCMessage("/unsubscribe")
        msg.appendTypedArg(self.own_address[0], "s")
        msg.appendTypedArg(self.own_address[1], "i")
        msg.appendTypedArg(self.args.authenticate, "s")
        self.osc_sock.sendto(msg.encode_osc(), self.chaosc_address)

    def run(self):

        while self.running:
            reads, writes, errs = select.select([self.osc_sock], [], [], 0.05)
            if reads:
                osc_input = reads[0].recv(4096)
                osc_address, typetags, messages = decode_osc(osc_input, 0, len(osc_input))
                if osc_address.find("ekg") > -1 or osc_address.find("plot") != -1:
                    queue.put_nowait((osc_address, messages))
            else:
                queue.put_nowait(("/bjoern/ekg", [0]))
                queue.put_nowait(("/merle/ekg", [0]))
                queue.put_nowait(("/uwe/ekg", [0]))
        self.unsubscribe_me()
        print "OSCThread is going down"


queue = Queue.Queue()

class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        print "get"

        self.thread = thread = OSCThread(self.server.args)
        thread.daemon = True
        thread.start()

        actors = list()
        is_item1 = True
        is_item2 = True
        is_item3 = True

        def setPositions():
            for ix, item in enumerate(actors):
                item.setPos(0, ix*6)


        def scale_data(data, ix, max_items):
            scale = 254 / max_items * ix
            return [value / max_items + scale for value in data]

        try:
            self.path=re.sub('[^.a-zA-Z0-9]', "",str(self.path))
            if self.path=="" or self.path==None or self.path[:1]==".":
                return

            if self.path.endswith(".html"):
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-type',    'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
            elif self.path.endswith(".mjpeg"):
                data_points = 1000

                self.send_response(200)
                plot_data1 = data = deque([0] * data_points)
                plot_data2 = data = deque([0] * data_points)
                plot_data3 = data = deque([0] * data_points)
                plt = PlotWidget(title="<h1>EKG</h1>", name="Merle")
                plt.hide()
                plotItem1 = pg.PlotCurveItem(pen=pg.mkPen('r', width=2), name="bjoern")
                plotItem2 = pg.PlotCurveItem(pen=pg.mkPen('g', width=2), name="merle")
                plotItem3 = pg.PlotCurveItem(pen=pg.mkPen('b', width=2), name="uwe")
                print type(plotItem1)
                pen = pg.mkPen(254, 254, 254)
                plotItem1.setShadowPen(pen=pen, width=6, cosmetic=True)
                plotItem2.setShadowPen(pen=pen, width=6, cosmetic=True)
                plotItem3.setShadowPen(pen=pen, width=6, cosmetic=True)
                actors.append(plotItem1)
                actors.append(plotItem2)
                actors.append(plotItem3)
                plotItem1.setPos(0, 0*6)
                plotItem2.setPos(0, 1*6)
                plotItem3.setPos(0, 2*6)
                plt.addItem(plotItem1)
                plt.addItem(plotItem2)
                plt.addItem(plotItem3)

                plt.setLabel('left', "<h2>Amplitude</h2>")
                plt.setLabel('bottom', "<h2>Time</h2>")
                plt.showGrid(True, True)
                ba = plt.getAxis("bottom")
                bl = plt.getAxis("left")
                ba.setTicks([])
                bl.setTicks([])
                plt.setYRange(0, 254)

                self.wfile.write("Content-Type: multipart/x-mixed-replace; boundary=--aaboundary")
                self.wfile.write("\r\n\r\n")


                plt.resize(1280, 720)

                while 1:
                    while 1:
                        try:
                            osc_address, args = queue.get_nowait()
                        except Queue.Empty:
                            break

                        value = args[0]
                        if osc_address == "/bjoern/ekg":
                            plot_data1.append(value)
                            plot_data1.popleft()
                            try:
                                plotItem1.setData(y=np.array(scale_data(plot_data1, actors.index(plotItem1), len(actors))), clear=True)
                            except ValueError:
                                pass
                        elif osc_address == "/merle/ekg":
                            plot_data2.append(value)
                            plot_data2.popleft()
                            try:
                                plotItem2.setData(y=np.array(scale_data(plot_data2, actors.index(plotItem2), len(actors))), clear=True)
                            except ValueError:
                                pass
                        elif osc_address == "/uwe/ekg":
                            plot_data3.append(value)
                            plot_data3.popleft()
                            try:
                                plotItem3.setData(y=np.array(scale_data(plot_data3, actors.index(plotItem3), len(actors))), clear=True)
                            except ValueError:
                                pass
                        elif osc_address == "/plot/uwe":
                            if value == 1 and is_item3 == False:
                                print "uwe on"
                                plt.addItem(plotItem3)
                                is_item3 = True
                                actors.append(plotItem3)
                                setPositions()
                            elif value == 0 and is_item3 == True:
                                print "uwe off"
                                plt.removeItem(plotItem3)
                                is_item3 = False
                                actors.remove(plotItem3)
                                setPositions()
                        elif osc_address == "/plot/merle":
                            if value == 1 and is_item2 == False:
                                print "merle on"
                                plt.addItem(plotItem2)
                                is_item2 = True
                                actors.append(plotItem2)
                                setPositions()
                            elif value == 0 and is_item2 == True:
                                print "merle off"
                                plt.removeItem(plotItem2)
                                is_item2 = False
                                actors.remove(plotItem2)
                                setPositions()
                        elif osc_address == "/plot/bjoern":
                            if value == 1 and is_item1 == False:
                                print "bjoern on"
                                plt.addItem(plotItem1)
                                is_item1 = True
                                actors.append(plotItem1)
                                setPositions()
                            elif value == 0 and is_item1 == True:
                                print "bjoern off"
                                plt.removeItem(plotItem1)
                                is_item1 = False
                                actors.remove(plotItem1)
                                setPositions()

                    exporter = pg.exporters.ImageExporter.ImageExporter(plt.plotItem)
                    img = exporter.export("tmpfile", True)
                    buffer = QBuffer()
                    buffer.open(QIODevice.WriteOnly)
                    img.save(buffer, "JPG", 100)
                    JpegData = buffer.data()
                    del buffer
                    self.wfile.write("--aaboundary\r\nContent-Type: image/jpeg\r\nContent-length: %d\r\n\r\n%s\r\n\r\n\r\n" % (len(JpegData), JpegData))

            elif self.path.endswith(".jpeg"):
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-type','image/jpeg')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
            return
        except (KeyboardInterrupt, SystemError):
            thread.running = False
            thread.join()
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)

    def __del__(self):
        self.thread.running = False
        self.thread.join()


class JustAHTTPServer(HTTPServer):
    pass


def main():
    a = create_arg_parser("ekgplotter")
    own_group = add_main_group(a)
    own_group.add_argument('-x', "--http_host", default=socket.gethostname(),
        help='my host, defaults to "socket.gethostname()"')
    own_group.add_argument('-X', "--http_port", default=9000,
        type=int, help='my port, defaults to 9000')
    add_chaosc_group(a)
    add_subscriber_group(a, "ekgplotter")
    args = finalize_arg_parser(a)

    try:
        host, port = socket.getaddrinfo(args.http_host, args.http_port, socket.AF_INET6, socket.SOCK_DGRAM, 0, socket.AI_V4MAPPED | socket.AI_ALL | socket.AI_CANONNAME)[-1][4][:2]

        server = JustAHTTPServer(("0.0.0.0", 9000), MyHandler)
        server.args = args
        print "%s: starting up http server on '%s:%d'" % (
            datetime.now().strftime("%x %X"), host, port)
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()


if __name__ == '__main__':
    main()

