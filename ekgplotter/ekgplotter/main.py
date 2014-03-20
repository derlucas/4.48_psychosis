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

    def __del__(self):
        self.thread.running = False
        self.thread.join()

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


        def set_point(plotPoint, pos, value, ix, max_items):
            scale = 254 / max_items * ix
            y = 6 * ix + value / max_items + scale
            plotPoint.setData(x = [pos], y = [y])


        def find_max_value(item_data):
            max_index = -1
            for ix, i in enumerate(item_data):
                if i > 250:
                    return ix, i
            return None, None


        def rearrange(item_data, actual_pos, max_items):
            max_value_index, max_value = find_max_value(item_data)
            if max_value_index is None:
                return actual_pos
            mean = int(max_items / 2.)
            start = mean - max_value_index
            if start != 0:
                item_data.rotate(start)
                pos = (actual_pos + start) % max_items
            else:
                pos = actual_pos
            print "rearrange", mean, start, actual_pos, pos, item_data
            return pos


        def set_value(item_data, pos, max_pos, value):
            print "setValue before", pos, None, max_pos, value, item_data, len(item_data)
            item_data[pos] = value
            new_pos = (pos + 1) % max_pos
            print "setValue after ", pos, new_pos, max_pos, value, item_data, len(item_data)
            return new_pos

        def resize(item_data, max_length, new_max_length, pos):
            print "resize", max_length, new_max_length
            if new_max_length < 15:
                return max_length, pos

            if new_max_length > max_length:
                pad = (new_max_length - max_length)
                print "pad", pad
                for i in range(pad):
                    if i % 2 == 0:
                        item_data.append(0)
                    else:
                        item_data.appendleft(0)
                        pos += 1
                return new_max_length, pos
            elif new_max_length < max_length:
                pad = (max_length - new_max_length)
                for i in range(pad):
                    if i % 2 == 0:
                        item_data.pop()
                        if pos >= new_max_length:
                            pos = 0
                    else:
                        item_data.popleft()
                        if pos > 0:
                            pos -= 1
                return new_max_length, pos
            return max_length, pos

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
                data_points = 21

                self.send_response(200)
                pos1 = 0
                pos2 = 0
                pos3 = 0

                lengths1 = [0]

                data1_max_value = 0
                data2_max_value = 0
                data3_max_value = 0

                data1_distance = data_points
                data2_distance = data_points
                data3_distance = data_points

                plot_data1 = deque([0] * data_points)
                plot_data2 = deque([0] * data_points)
                plot_data3 = deque([0] * data_points)
                plt = PlotWidget(title="<h1>EKG</h1>")
                plt.hide()
                plotItem1 = pg.PlotCurveItem(pen=pg.mkPen('r', width=2), width=2, name="bjoern")
                plotItem2 = pg.PlotCurveItem(pen=pg.mkPen('g', width=2), width=2, name="merle")
                plotItem3 = pg.PlotCurveItem(pen=pg.mkPen('b', width=2), width=2, name="uwe")
                shadowPen = pg.mkPen("w", width=10)
                plotItem1.setShadowPen(pen=shadowPen, width=6, cosmetic=True)
                plotItem2.setShadowPen(pen=shadowPen, width=6, cosmetic=True)
                plotItem3.setShadowPen(pen=shadowPen, width=6, cosmetic=True)
                pen = pg.mkPen("w", size=1)
                brush = pg.mkBrush("w")
                plotPoint1 = pg.ScatterPlotItem(pen=pen, brush=brush, size=10)
                plotPoint2 = pg.ScatterPlotItem(pen=pen, brush=brush, size=10)
                plotPoint3 = pg.ScatterPlotItem(pen=pen, brush=brush, size=10)
                actors.append(plotItem1)
                actors.append(plotItem2)
                actors.append(plotItem3)
                plotItem1.setPos(0, 0*6)
                plotItem2.setPos(0, 1*6)
                plotItem3.setPos(0, 2*6)
                plt.addItem(plotItem1)
                plt.addItem(plotItem2)
                plt.addItem(plotItem3)
                plt.addItem(plotPoint1)
                plt.addItem(plotPoint2)
                plt.addItem(plotPoint3)

                plt.setLabel('left', "<h2>Amplitude</h2>")
                plt.setLabel('bottom', "<h2><sup>Time</sup></h2>")
                plt.showGrid(True, True)
                ba = plt.getAxis("bottom")
                bl = plt.getAxis("left")
                ba.setTicks([])
                bl.setTicks([])
                ba.setWidth(0)
                ba.setHeight(0)
                bl.setWidth(0)
                bl.setHeight(0)
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
                        max_items = len(actors)
                        value = args[0]

                        if osc_address == "/bjoern/ekg":
                            if value > 250:
                                data_points, pos1 = resize(plot_data1, len(plot_data1), lengths1[-1], pos1)
                                foo, pos2 = resize(plot_data2, len(plot_data2), lengths1[-1], pos2)
                                foo, pos3 = resize(plot_data3, len(plot_data3), lengths1[-1], pos3)
                                print "length1", lengths1
                                lengths1.append(0)
                            else:
                                lengths1[-1] += 1

                            ix = actors.index(plotItem1)

                            pos1 = rearrange(plot_data1, pos1, data_points)
                            set_point(plotPoint1, pos1, value, ix, max_items)
                            pos1 = set_value(plot_data1, pos1, data_points, value)
                            try:
                                plotItem1.setData(y=np.array(scale_data(plot_data1, ix, max_items)), clear=True)
                            except ValueError:
                                pass

                        elif osc_address == "/merle/ekg":
                            ix = actors.index(plotItem2)

                            pos2 = rearrange(plot_data2, pos2, data_points)
                            set_point(plotPoint2, pos2, value, ix, max_items)
                            pos2 = set_value(plot_data2, pos2, data_points, value)
                            try:
                                plotItem2.setData(y=np.array(scale_data(plot_data2, ix, max_items)), clear=True)
                            except ValueError:
                                pass
                        elif osc_address == "/uwe/ekg":
                            ix = actors.index(plotItem3)
                            pos3 = rearrange(plot_data3, pos3, data_points)
                            set_point(plotPoint3, pos3, value, ix, max_items)
                            pos3 = set_value(plot_data3, pos3, data_points, value)
                            try:
                                plotItem3.setData(y=np.array(scale_data(plot_data3, ix, max_items)), clear=True)
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


class JustAHTTPServer(HTTPServer):
    pass


def main():
    a = create_arg_parser("ekgplotter")
    own_group = add_main_group(a)
    own_group.add_argument('-x', "--http_host", default="0.0.0.0",
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

