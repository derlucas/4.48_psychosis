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

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from chaosc.argparser_groups import *
from chaosc.lib import logger, resolve_host
from datetime import datetime
from operator import attrgetter
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QBuffer, QByteArray, QIODevice
from SocketServer import ThreadingMixIn, ForkingMixIn

import logging
import numpy as np
import os.path
import pyqtgraph as pg
import Queue
import re
import select
import socket
import threading
import time


try:
    from chaosc.c_osc_lib import OSCMessage, decode_osc
except ImportError as e:
    logging.exception(e)
    from chaosc.osc_lib import OSCMessage, decode_osc


class OSCThread(threading.Thread):
    def __init__(self, args):
        super(OSCThread, self).__init__()
        self.args = args
        self.running = True

        self.client_address = resolve_host(args.client_host, args.client_port, args.address_family)

        self.chaosc_address = chaosc_host, chaosc_port = resolve_host(args.chaosc_host, args.chaosc_port, args.address_family)

        self.osc_sock = socket.socket(args.address_family, 2, 17)
        self.osc_sock.bind(self.client_address)
        self.osc_sock.setblocking(0)

        logger.info("%s: starting up osc receiver on '%s:%d'",
            datetime.now().strftime("%x %X"), self.client_address[0], self.client_address[1])

        self.subscribe_me()

    def subscribe_me(self):
        logger.info("%s: subscribing to '%s:%d' with label %r", datetime.now().strftime("%x %X"), self.chaosc_address[0], self.chaosc_address[1], self.args.subscriber_label)
        msg = OSCMessage("/subscribe")
        msg.appendTypedArg(self.client_address[0], "s")
        msg.appendTypedArg(self.client_address[1], "i")
        msg.appendTypedArg(self.args.authenticate, "s")
        if self.args.subscriber_label is not None:
            msg.appendTypedArg(self.args.subscriber_label, "s")
        self.osc_sock.sendto(msg.encode_osc(), self.chaosc_address)


    def unsubscribe_me(self):
        if self.args.keep_subscribed:
            return

        logger.info("%s: unsubscribing from '%s:%d'", datetime.now().strftime("%x %X"), self.chaosc_address[0], self.chaosc_address[1])
        msg = OSCMessage("/unsubscribe")
        msg.appendTypedArg(self.client_address[0], "s")
        msg.appendTypedArg(self.client_address[1], "i")
        msg.appendTypedArg(self.args.authenticate, "s")
        self.osc_sock.sendto(msg.encode_osc(), self.chaosc_address)

    def run(self):

        while self.running:
            try:
                reads, writes, errs = select.select([self.osc_sock], [], [], 0.005)
            except Exception, e:
                logging.exception(e)
                pass
            else:
                if reads:
                    try:
                        osc_input, address = self.osc_sock.recvfrom(8192)
                        osc_address, typetags, messages = decode_osc(osc_input, 0, len(osc_input))
                        queue.put_nowait((osc_address, messages))
                    except Exception, e:
                        logger.info(e)

        self.unsubscribe_me()
        self.osc_sock.close()
        logger.info("OSCThread is going down")


queue = Queue.Queue()

class Actor(object):
    def __init__(self, name, num_data, color, ix, max_actors, actor_height):
        self.name = name
        self.num_data = num_data
        self.color = color
        self.ix = ix
        self.max_actors = max_actors
        self.actor_height = actor_height
        self.updated = 0

        self.offset = ix * actor_height
        self.data = np.array([self.offset] * num_data)
        self.head = 0
        self.pre_head = 0
        self.plotItem = pg.PlotCurveItem(pen=pg.mkPen(color, width=3), name=name)
        self.plotPoint = pg.ScatterPlotItem(pen=pg.mkPen("w", width=5), brush=pg.mkBrush(color), size=5)

    def __str__(self):
        return "<Actor name:%r, active=%r, position=%r>" % (self.name, self.active, self.head)

    __repr__ = __str__


    def add_value(self, value):
        dp = self.head
        self.data[dp] = value / self.max_actors + self.offset
        self.pre_head = dp
        self.head = (dp + 1) % self.num_data
        self.updated += 1

    def fill_missing(self, count):
        dp = self.head
        for i in range(count):
            self.data[dp] = self.offset
            dp = (dp + 1) % self.num_data
            self.updated += 1

        self.pre_head = (dp - 1) % self.num_data
        self.head = dp

    def render(self):
        self.plotItem.setData(y=self.data, clear=True)
        self.plotPoint.setData(x=[self.pre_head], y = [self.data[self.pre_head]])


class EkgPlot(object):
    def __init__(self, actor_names, num_data, colors):
        self.plot = pg.PlotWidget()
        #self.plot.setConfigOptions(antialias=True)
        self.plot.hide()
        self.plot.showGrid(False, False)
        self.plot.setYRange(0, 255)
        self.plot.setXRange(0, num_data)
        self.plot.resize(768, 576)

        ba = self.plot.getAxis("bottom")
        bl = self.plot.getAxis("left")
        ba.setTicks([])
        bl.setTicks([])
        ba.hide()
        bl.hide()
        self.active_actors = list()

        self.actors = dict()
        self.lengths1 = [0]
        self.num_data = num_data

        self.max_value = 255
        self.max_actors = len(actor_names)
        self.actor_height = self.max_value / self.max_actors
        for ix, (actor_name, color) in enumerate(zip(actor_names, colors)):
            self.add_actor(actor_name, num_data, color, ix, self.max_actors, self.actor_height)

        self.set_positions()

        self.ekg_regex = re.compile("^/(.*?)/ekg$")
        self.ctl_regex = re.compile("^/plot/(.*?)$")
        self.updated_actors = set()


    def add_actor(self, actor_name, num_data, color, ix, max_actors, actor_height):
        actor_obj = Actor(actor_name, num_data, color, ix, max_actors, actor_height)
        self.actors[actor_name] = actor_obj
        self.plot.addItem(actor_obj.plotItem)
        self.plot.addItem(actor_obj.plotPoint)
        self.active_actors.append(actor_obj)


    def set_positions(self):
        for ix, actor_obj in enumerate(self.active_actors):
            actor_obj.plotItem.setPos(0, ix * 2)
            actor_obj.plotPoint.setPos(0, ix * 2)

    def active_actor_count(self):
        return self.max_actors

    def new_round(self):
        for ix, actor in enumerate(self.active_actors):
            actor.updated = 0

    def update_missing_actors(self):
        liste = sorted(self.active_actors, key=attrgetter("updated"))
        max_values = liste[-1].updated
        if max_values == 0:
            # handling no signal
            for actor in self.active_actors:
                actor.add_value(0)
            return
        for ix, actor in enumerate(self.active_actors):
            diff = max_values - actor.updated
            if diff > 0:
                for i in range(diff):
                    actor.add_value(0)


    def update(self, osc_address, value):

        res = self.ekg_regex.match(osc_address)
        if res:
            actor_name = res.group(1)
            actor_obj = self.actors[actor_name]
            actor_obj.add_value(value)


    def render(self):
        for ix, actor in enumerate(self.active_actors):
            actor.render()


class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        try:
            self.path=re.sub('[^.a-zA-Z0-9]', "",str(self.path))
            if self.path=="" or self.path==None or self.path[:1]==".":
                self.send_error(403,'Forbidden')

            if self.path.endswith(".html"):
                directory = os.path.dirname(os.path.abspath(__file__))
                data = open(os.path.join(directory, self.path), "rb").read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(data)
            elif self.path.endswith(".mjpeg"):
                self.thread = thread = OSCThread(self.server.args)
                thread.daemon = True
                thread.start()
                actor_names = ["bjoern", "uwe", "merle"]
                num_data = 100
                colors = ["r", "g", "b"]
                qtapp = QtGui.QApplication([])
                plotter = EkgPlot(actor_names, num_data, colors)

                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=--2342")
                self.end_headers()
                event_loop = QtCore.QEventLoop()
                last_frame = time.time() - 1.0
                frame_rate = 13.0
                frame_length = 1. / frame_rate
                plotter.new_round()
                while 1:
                    event_loop.processEvents()
                    qtapp.sendPostedEvents(None, 0)
                    while 1:
                        try:
                            osc_address, args = queue.get_nowait()
                            plotter.update(osc_address, args[0])
                        except Queue.Empty:
                            break

                    now = time.time()
                    delta = now - last_frame
                    if delta > frame_length:
                        plotter.update_missing_actors()
                        plotter.render()
                        exporter = pg.exporters.ImageExporter.ImageExporter(plotter.plot.plotItem)
                        exporter.parameters()['width'] = 768
                        img = exporter.export(toBytes=True)
                        buffer = QBuffer()
                        buffer.open(QIODevice.WriteOnly)
                        img.save(buffer, "JPG")
                        JpegData = buffer.data()
                        self.wfile.write("--2342\r\nContent-Type: image/jpeg\r\nContent-length: %d\r\n\r\n%s\r\n\r\n\r\n" % (len(JpegData), JpegData))
                        last_frame = now
                        plotter.new_round()
                        #JpegData = None
                        #buffer = None
                        #img = None
                        #exporter = None
                    time.sleep(0.01)

        except (KeyboardInterrupt, SystemError), e:
            raise e
        except IOError, e:
            if e[0] in (32, 104):
                if hasattr(self, "thread") and self.thread is not None:
                    self.thread.running = False
                    self.thread.join()
                    self.thread = None
            else:
                pass


class JustAHTTPServer(HTTPServer):
    pass


def main():
    arg_parser = ArgParser("ekgplotter")
    arg_parser.add_global_group()
    client_group = arg_parser.add_client_group()
    arg_parser.add_argument(client_group, '-x', "--http_host", default="::",
        help='my host, defaults to "::"')
    arg_parser.add_argument(client_group, '-X', "--http_port", default=9000,
        type=int, help='my port, defaults to 9000')
    arg_parser.add_chaosc_group()
    arg_parser.add_subscriber_group()
    args = arg_parser.finalize()

 
    http_host, http_port = resolve_host(args.http_host, args.http_port, args.address_family)

    server = JustAHTTPServer((http_host, http_port), MyHandler)
    server.address_family = args.address_family
    server.args = args
    logger.info("%s: starting up http server on '%s:%d'",
        datetime.now().strftime("%x %X"), http_host, http_port)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info('^C received, shutting down server')
        server.socket.close()
        sys.exit(0)

if __name__ == '__main__':
    main()
