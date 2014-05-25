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

from chaosc.argparser_groups import *
from chaosc.lib import logger, resolve_host
from datetime import datetime
from operator import attrgetter
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QBuffer, QByteArray, QIODevice
from PyQt4.QtNetwork import QTcpServer, QTcpSocket, QUdpSocket, QHostAddress
from PyQt4.QtGui import QPixmap

import logging
import numpy as np
import os.path
import pyqtgraph as pg
from pyqtgraph.widgets.PlotWidget import PlotWidget
import Queue
import re
import select
import socket
import threading
import time

from psylib.mjpeg_streaming_server import MjpegStreamingServer


try:
    from chaosc.c_osc_lib import OSCMessage, decode_osc
except ImportError as e:
    logging.exception(e)
    from chaosc.osc_lib import OSCMessage, decode_osc


def get_steps(pulse_rate, rate):
    beat_length = 60. / pulse_rate
    steps_pre =  int(beat_length / rate) + 1
    used_sleep_time = beat_length / steps_pre
    steps = int(beat_length / used_sleep_time)
    return steps, used_sleep_time


class Generator(object):
    def __init__(self, pulse=92, delta=0.08):
        self.count = 0
        self.pulse = 92
        self.delta = delta
        self.steps = get_steps(self.pulse, delta / 2)

    def __call__(self):
        while 1:
            value = random.randint(0, steps)
            if self.count < int(steps / 100. * 20):
                value = random.randint(0,20)
            elif self.count < int(steps / 100. * 30):
                value = random.randint(20, 30)
            elif self.count < int(steps / 100. * 40):
                value = random.randint(30,100)
            elif self.count < int(steps / 2.):
                value = random.randint(100,200)
            elif self.count == int(steps / 2.):
                value = 255
            elif self.count < int(steps / 100. * 60):
                value = random.randint(100, 200)
            elif self.count < int(steps / 100. * 70):
                value = random.randint(50, 100)
            elif self.count < int(steps / 100. * 80):
                value = random.randint(20, 50)
            elif self.count <= steps:
                value = random.randint(0,20)
            elif self.count >= steps:
                self.count = 0

            self.count += 1
            yield value

    def retrigger(self):
        self.count = self.steps / 2


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


class EkgPlotWidget(PlotWidget):
    def __init__(self, args, parent=None):
        super(EkgPlotWidget, self).__init__(parent)
        self.args = args

        self.http_server = MjpegStreamingServer((args.http_host, args.http_port), self)
        self.http_server.listen(port=args.http_port)

        self.osc_sock = QUdpSocket(self)
        logger.info("osc bind localhost %d", args.client_port)
        self.osc_sock.bind(QHostAddress("127.0.0.1"), args.client_port)
        self.osc_sock.readyRead.connect(self.got_message)
        self.osc_sock.error.connect(self.handle_osc_error)
        msg = OSCMessage("/subscribe")
        msg.appendTypedArg("localhost", "s")
        msg.appendTypedArg(args.client_port, "i")
        msg.appendTypedArg(self.args.authenticate, "s")
        if self.args.subscriber_label is not None:
            msg.appendTypedArg(self.args.subscriber_label, "s")
        self.osc_sock.writeDatagram(QByteArray(msg.encode_osc()), QHostAddress("127.0.0.1"), 7110)
        self.num_data = 100

        self.hide()
        self.showGrid(False, False)
        self.setYRange(0, 255)
        self.setXRange(0, self.num_data)
        self.resize(768, 576)


        colors = ["r", "g", "b"]

        ba = self.getAxis("bottom")
        bl = self.getAxis("left")
        ba.setTicks([])
        bl.setTicks([])
        ba.hide()
        bl.hide()
        self.active_actors = list()

        self.actors = dict()
        self.lengths1 = [0]

        self.max_value = 255
        actor_names = ["merle", "uwe", "bjoern" ]
        self.max_actors = len(actor_names)
        self.actor_height = self.max_value / self.max_actors

        for ix, (actor_name, color) in enumerate(zip(actor_names, colors)):
            self.add_actor(actor_name, self.num_data, color, ix, self.max_actors, self.actor_height)

        self.set_positions()

        self.ekg_regex = re.compile("^/(.*?)/ekg$")
        self.ctl_regex = re.compile("^/plot/(.*?)$")
        self.updated_actors = set()
        self.new_round()


    def add_actor(self, actor_name, num_data, color, ix, max_actors, actor_height):
        actor_obj = Actor(actor_name, num_data, color, ix, max_actors, actor_height)
        self.actors[actor_name] = actor_obj
        self.addItem(actor_obj.plotItem)
        self.addItem(actor_obj.plotPoint)
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

    def closeEvent(self, event):
        msg = OSCMessage("/unsubscribe")
        msg.appendTypedArg("localhost", "s")
        msg.appendTypedArg(self.args.client_port, "i")
        msg.appendTypedArg(self.args.authenticate, "s")
        self.osc_sock.writeDatagram(QByteArray(msg.encode_osc()), QHostAddress("127.0.0.1"), 7110)

    def handle_osc_error(self, error):
        logger.info("osc socket error %d", error)

    def render_image(self):
        self.update_missing_actors()
        self.render()
        exporter = pg.exporters.ImageExporter.ImageExporter(self.plotItem)
        exporter.parameters()['width'] = 768
        img = exporter.export(toBytes=True)
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        img.save(buf, "JPG", 75)
        JpegData = buf.data()
        self.new_round()
        return JpegData

    def got_message(self):
        while self.osc_sock.hasPendingDatagrams():
            data, address, port = self.osc_sock.readDatagram(self.osc_sock.pendingDatagramSize())
            try:
                osc_address, typetags, args = decode_osc(data, 0, len(data))
            except Exception, e:
                logger.exception(e)
                return
            else:
                self.update(osc_address, args[0])
        return True



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

    args.http_host, args.http_port = resolve_host(args.http_host, args.http_port, args.address_family)

    qtapp = QtGui.QApplication([])
    widget = EkgPlotWidget(args)
    qtapp.exec_()


if __name__ == '__main__':
    main()
