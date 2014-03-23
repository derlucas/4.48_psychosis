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


#import objgraph

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
from chaosc.lib import resolve_host

#try:
    #from chaosc.c_osc_lib import *
#except ImportError:
from chaosc.osc_lib import *

QtGui.QApplication.setGraphicsSystem('opengl')

print "systemInfo", pg.systemInfo()

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

        self.osc_sock = socket.socket(10, 2, 17)
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
                #print "thread osc_address", osc_address
                if osc_address.find("ekg") > -1 or osc_address.find("plot") != -1:
                    queue.put_nowait((osc_address, messages))
            else:
                queue.put_nowait(("/bjoern/ekg", [0]))
                queue.put_nowait(("/merle/ekg", [0]))
                queue.put_nowait(("/uwe/ekg", [0]))
        self.unsubscribe_me()
        print "OSCThread is going down"


queue = Queue.Queue()

class Actor(object):
    shadowPen = pg.mkPen(255, 255, 255)
    brush = pg.mkBrush("w")
    def __init__(self, name, num_data, color):
        self.data = [0] * num_data
        self.data_pointer = 0
        self.name = name
        self.active = True
        self.plotItem = pg.PlotCurveItem(pen=pg.mkPen(color, width=3), name=name)
        self.num_data = num_data
        #self.plotItem.setShadowPen(pen=Actor.shadowPen, width=3, cosmetic=True)
        self.plotPoint = pg.ScatterPlotItem(pen=Actor.shadowPen, brush=self.brush, size=5)


    def scale_data(self, ix, max_items):
        scale = 255 / max_items * ix
        return [value / max_items + scale for value in self.data]

    def set_point(self, value, ix, max_items):
        scale = 255 / max_items * ix
        self.plotPoint.setData(x = [self.data_pointer], y = [value / max_items + scale])

    #def find_max_value(self, item_data):
            #max_index = -1
            #for ix, i in enumerate(item_data):
                #if i > 250:
                    #return ix, i
            #return None, None


    #def rearrange(self, item_data, actual_pos, max_items):
        #max_value_index, max_value = find_max_value(item_data)
        #if max_value_index is None:
            #return actual_pos
        #mean = int(max_items / 2.)
        #start = mean - max_value_index
        #if start != 0:
            #item_data.rotate(start)
            #pos = (actual_pos + start) % max_items
        #else:
            #pos = actual_pos
        #print "rearrange", mean, start, actual_pos, pos, item_data
        #return pos


    def set_value(self, value):
        self.data[self.data_pointer] = value
        self.data_pointer = (self.data_pointer + 1) % self.num_data

    #def resize(item_data, max_length, new_max_length, pos):
        #print "resize", max_length, new_max_length
        #if new_max_length < 15:
            #return max_length, pos

        #if new_max_length > max_length:
            #pad = (new_max_length - max_length)
            #print "pad", pad
            #for i in range(pad):
                #if i % 2 == 0:
                    #item_data.append(0)
                #else:
                    #item_data.appendleft(0)
                    #pos += 1
            #return new_max_length, pos
        #elif new_max_length < max_length:
            #pad = (max_length - new_max_length)
            #for i in range(pad):
                #if i % 2 == 0:
                    #item_data.pop()
                    #if pos >= new_max_length:
                        #pos = 0
                #else:
                    #item_data.popleft()
                    #if pos > 0:
                        #pos -= 1
            #return new_max_length, pos
        #return max_length, pos

class EkgPlot(object):
    def __init__(self, actor_names, num_data, colors):

        self.plot = pg.PlotWidget(title="<h1>EKG</h1>")
        self.plot.hide()
        self.plot.setLabel('left', "<h2>Amplitude</h2>")
        self.plot.setLabel('bottom', "<h2><sup>Time</sup></h2>")
        self.plot.showGrid(True, True)
        self.plot.setYRange(0, 255)
        self.plot.setXRange(0, num_data)
        self.plot.resize(1280, 720)

        ba = self.plot.getAxis("bottom")
        bl = self.plot.getAxis("left")
        ba.setTicks([])
        bl.setTicks([])
        self.active_actors = list()

        self.actors = dict()
        self.lengths1 = [0]
        self.num_data = num_data

        for actor_name, color in zip(actor_names, colors):
            self.add_actor(actor_name, num_data, color)

        self.set_positions()

        self.ekg_regex = re.compile("^/(.*?)/ekg$")
        self.ctl_regex = re.compile("^/plot/(.*?)$")
        self.updated_actors = set()


    def add_actor(self, actor_name, num_data, color):
        actor_obj = Actor(actor_name, num_data, color)
        self.actors[actor_name] = actor_obj
        self.plot.addItem(actor_obj.plotItem)
        self.plot.addItem(actor_obj.plotPoint)
        self.active_actors.append(actor_obj)


    def set_positions(self):
        for ix, actor_obj in enumerate(self.active_actors):
            actor_obj.plotItem.setPos(0, ix * 6)
            actor_obj.plotPoint.setPos(0, ix * 6)

    def active_actor_count(self):
        return len(self.active_actors)

    def update(self, osc_address, value):

        res = self.ekg_regex.match(osc_address)
        if res:
            actor_name = res.group(1)
            actor_obj = self.actors[actor_name]
            max_actors = len(self.active_actors)
            ix = self.active_actors.index(actor_obj)
            actor_data = actor_obj.data
            data_pointer = actor_obj.data_pointer
            actor_data[data_pointer] = value
            actor_obj.set_point(value, ix, max_actors)
            actor_obj.data_pointer = (data_pointer + 1) % self.num_data
            actor_obj.plotItem.setData(y=np.array(actor_obj.scale_data(ix, max_actors)), clear=True)
            return

        res = self.ctl_regex.match(osc_address)
        if res:
            actor_name = res.group(1)
            actor_obj = self.actors[actor_name]
            if value == 1 and not actor_obj.active:
                print "actor on", actor_name
                self.plot.addItem(actor_obj)
                actor_obj.active = True
                self.active_actors.append(actor_obj)
            elif value == 0 and not actor_obj.active:
                print "actor off", actor_name
                self.plot.removeItem(actor_obj)
                actor_obj.active = True
                self.active_actors.remove(actor_obj)

            self.set_positions()


class MyHandler(BaseHTTPRequestHandler):

    def __del__(self):
        self.thread.running = False
        self.thread.join()

    def do_GET(self):

        try:
            self.path=re.sub('[^.a-zA-Z0-9]', "",str(self.path))
            if self.path=="" or self.path==None or self.path[:1]==".":
                self.send_error(403,'Forbidden')


            if self.path.endswith(".html"):
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-type',    'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
            elif self.path.endswith(".mjpeg"):
                self.thread = thread = OSCThread(self.server.args)
                thread.daemon = True
                thread.start()

                self.send_response(200)
                actor_names = ["bjoern", "merle", "uwe"]
                num_data = 100
                colors = ["r", "g", "b"]
                plotter = EkgPlot(actor_names, num_data, colors)


                self.wfile.write("Content-Type: multipart/x-mixed-replace; boundary=--aaboundary\r\n\r\n")
                #lastTime = time.time()
                #fps = None
                while 1:
                    while 1:
                        try:
                            osc_address, args = queue.get_nowait()
                        except Queue.Empty:
                            break

                        plotter.update(osc_address, args[0])

                    exporter = pg.exporters.ImageExporter.ImageExporter(plotter.plot.plotItem)
                    img = exporter.export("tmpfile", True)
                    buffer = QBuffer()
                    buffer.open(QIODevice.WriteOnly)
                    img.save(buffer, "JPG", 100)
                    JpegData = buffer.data()
                    self.wfile.write("--aaboundary\r\nContent-Type: image/jpeg\r\nContent-length: %d\r\n\r\n%s\r\n\r\n\r\n" % (len(JpegData), JpegData))
                    del JpegData
                    del buffer
                    del img
                    del exporter
                    #now = time.time()
                    #dt = now - lastTime
                    #lastTime = now
                    #if fps is None:
                        #fps = 1.0/dt
                    #else:
                        #s = np.clip(dt*3., 0, 1)
                        #fps = fps * (1-s) + (1.0/dt) * s
                    #print '%0.2f fps' % fps

            elif self.path.endswith(".jpeg"):
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-type','image/jpeg')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
            return
        except (KeyboardInterrupt, SystemError):
            print "queue size", queue.qsize()
            thread.running = False
            thread.join()
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)


class JustAHTTPServer(HTTPServer):
    address_family = socket.AF_INET6
    pass


def main():
    a = create_arg_parser("ekgplotter")
    own_group = add_main_group(a)
    own_group.add_argument('-x', "--http_host", default="::",
        help='my host, defaults to "socket.gethostname()"')
    own_group.add_argument('-X', "--http_port", default=9000,
        type=int, help='my port, defaults to 9000')
    add_chaosc_group(a)
    add_subscriber_group(a, "ekgplotter")
    args = finalize_arg_parser(a)


    http_host, http_port = resolve_host(args.http_host, args.http_port)
    print http_host, http_port

    server = JustAHTTPServer((http_host, http_port), MyHandler)
    server.args = args
    print "%s: starting up http server on '%s:%d'" % (
        datetime.now().strftime("%x %X"), http_host, http_port)

    print "before start:"
    #objgraph.show_growth()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        #print "queue size", queue.qsize()
        #print "show growth", objgraph.show_growth()
        #import random
        #objgraph.show_chain(
            #objgraph.find_backref_chain(
                #random.choice(objgraph.by_type('function')),
                #objgraph.is_proper_module),
            #filename='chain.png')
        #roots = objgraph.get_leaking_objects()
        #print "root", len(roots)
        #objgraph.show_most_common_types(objects=roots)
        #objgraph.show_refs(roots[:3], refcounts=True, filename='roots.png')
        server.socket.close()


if __name__ == '__main__':
    main()

