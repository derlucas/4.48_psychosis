#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of psychose/ekgplotter package
#
# psychose/ekgplotter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# psychose/ekgplotter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with psychose/ekgplotter.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2014 Stefan Kögl

from __future__ import absolute_import

import random
import os.path
import re
import signal
import sys
import exceptions

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QImage, QPixmap, QMainWindow
from PyQt4.QtCore import QBuffer, QIODevice

import numpy as np

import pyqtgraph as pg
from pyqtgraph.widgets.PlotWidget import PlotWidget
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
from pyqtgraph.graphicsItems.ScatterPlotItem import ScatterPlotItem

from chaosc.argparser_groups import ArgParser
from chaosc.lib import logger, resolve_host
from psylib.mjpeg_streaming_server import *
from psylib.psyqt_base import PsyQtChaoscClientBase

try:
    from chaosc.c_osc_lib import decode_osc
except ImportError as e:
    from chaosc.osc_lib import decode_osc

qtapp = QtGui.QApplication([])


def get_steps(pulse, delta_ms):
    beat_length = 60000. / pulse
    steps_pre = int(beat_length / delta_ms) + 1
    used_sleep_time = beat_length / steps_pre
    steps = int(beat_length / used_sleep_time)
    return steps, used_sleep_time


class Generator(object):
    def __init__(self, pulse=92, delta=80):
        self.count = 0
        self.pulse = random.randint(85, 105)
        self.delta = delta
        self.finished = False
        self.steps, _ = get_steps(self.pulse, delta / 4)

    def __call__(self):
        while 1:
            if self.count < int(self.steps / 100. * 30):
                value = random.randint(30, 35)
            elif self.count == int(self.steps / 100. * 30):
                value = random.randint(55, 66)
            elif self.count < int(self.steps / 100. * 45):
                value = random.randint(30, 35)
            elif self.count < int(self.steps / 2.):
                value = random.randint(0, 15)
            elif self.count == int(self.steps / 2.):
                value = 255
            elif self.count < int(self.steps / 100. * 60):
                value = random.randint(25, 35)
            elif self.count < int(self.steps / 100. * 70):
                value = random.randint(10, 30)
            elif self.count < self.steps:
                value = random.randint(15, 30)
            else:
                self.finished = True
                self.count = 0
                value = 30

            self.count += 1
            yield value

    def set_pulse(self, pulse):
        self.pulse = pulse
        self.steps, _ = get_steps(pulse, self.delta)

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
        self.offset = ix * actor_height
        self.data = np.array([self.offset + 30] * num_data)
        self.head = 0
        self.pre_head = 0
        self.plotItem = PlotCurveItem(pen=pg.mkPen(color, width=3), width=4, name=name)
        self.plotPoint = ScatterPlotItem(pen=pg.mkPen("w", width=5), brush=pg.mkBrush(color), size=5)
        self.osci = None
        self.osci_obj = None
        self.render()

    def __str__(self):
        return "<Actor name:%r, position=%r>" % (self.name, self.head)

    def __repr__(self):
        return "Actor(%r, %r, %r, %r, %r, %r)" % (self.name, self.num_data,
            self.color, self.ix, self.max_actors, self.actor_height)

    def add_value(self, value):
        self.pre_head = self.head
        self.data[self.pre_head] = value / self.max_actors + self.offset
        self.head = (self.pre_head + 1) % self.num_data

    def fill_missing(self, count):
        dp = self.head
        for i in range(count):
            self.data[dp] = self.offset
            dp = (dp + 1) % self.num_data

        self.pre_head = (dp - 1) % self.num_data
        self.head = dp

    def render(self):
        self.plotItem.setData(y=self.data, clear=True)
        self.plotPoint.setData(x=[self.pre_head], y=[self.data[self.pre_head]])

class PlotWindow(PlotWidget):
    def __init__(self, title=None, **kargs):
        self.win = QtGui.QMainWindow()
        self.win.resize(768, 576)
        PlotWidget.__init__(self, **kargs)
        self.win.setCentralWidget(self)
        for m in ['resize']:
            setattr(self, m, getattr(self.win, m))
        if title is not None:
            self.win.setWindowTitle(title)
        self.win.show()


class EkgPlotWidget(QMainWindow, PsyQtChaoscClientBase, MjpegStreamingConsumerInterface):
    def __init__(self, args, parent=None):
        self.args = args
        super(EkgPlotWidget, self).__init__()
        PsyQtChaoscClientBase.__init__(self)
        self.plot_widget = PlotWidget(title="Psychose - EkgPlotter")
        colors = ["r", "g", "b"]
        self.active_actors = list()
        self.actors = dict()
        self.max_value = 255
        actor_names = ["merle", "uwe", "bjoern"]
        self.max_actors = len(actor_names)
        self.actor_height = self.max_value / self.max_actors
        self.fps = 12.5
        self.http_server = MjpegStreamingServer((args.http_host, args.http_port), self, self.fps)
        self.http_server.listen(port=args.http_port)
        self.num_data = 100
        self.plot_widget.showGrid(False, False)
        self.plot_widget.setYRange(0, 255)
        self.plot_widget.setXRange(0, self.num_data)
        self.plot_widget.resize(768, 576)

        bottom_axis = self.plot_widget.getAxis("bottom")
        left_axis = self.plot_widget.getAxis("left")
        bottom_axis.setTicks([])
        left_axis.setTicks([])
        bottom_axis.hide()
        left_axis.hide()

        for ix, (actor_name, color) in enumerate(zip(actor_names, colors)):
            self.add_actor(actor_name, self.num_data, color, ix, self.max_actors, self.actor_height)

        self.set_positions()
        self.heartbeat_regex = re.compile("^/(.*?)/heartbeat$")

    def pubdir(self):
        return os.path.dirname(os.path.abspath(__file__))

    def add_actor(self, actor_name, num_data, color, ix, max_actors, actor_height):
        actor_obj = Actor(actor_name, num_data, color, ix, max_actors, actor_height)
        self.actors[actor_name] = actor_obj
        self.plot_widget.addItem(actor_obj.plotItem)
        self.plot_widget.addItem(actor_obj.plotPoint)
        self.active_actors.append(actor_obj)
        actor_obj.osci_obj = Generator(pulse=random.randint(88, 104), delta=self.http_server.timer_delta)
        actor_obj.osci = actor_obj.osci_obj()

    def set_positions(self):
        for ix, actor_obj in enumerate(self.active_actors):
            actor_obj.plotItem.setPos(0, ix * 2)
            actor_obj.plotPoint.setPos(0, ix * 2)

    def active_actor_count(self):
        return self.max_actors

    def update(self, osc_address, args):
        res = self.heartbeat_regex.match(osc_address)
        if res:
            actor_name = res.group(1)
            actor_obj = self.actors[actor_name]
            #logger.info("actor: %r, %r", actor_name, args)
            if args[0] == 1:
                actor_obj.osci_obj.retrigger()
            actor_obj.osci_obj.set_pulse(args[1])

    def render_image(self):
        for actor_obj in self.active_actors:
            actor_obj.add_value(actor_obj.osci.next())
            actor_obj.add_value(actor_obj.osci.next())
            actor_obj.add_value(actor_obj.osci.next())
            actor_obj.add_value(actor_obj.osci.next())
            actor_obj.render()
        image = QPixmap(768, 576)
        image.fill(QtCore.Qt.white)
        painter = QtGui.QPainter(image)
        painter.setRenderHints(QtGui.QPainter.RenderHint(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing),
            True)
        scene = self.plot_widget.plotItem.scene()
        scene.render(painter, QtCore.QRectF(0, 0, 768, 576), QtCore.QRectF(0, 0, 768, 576))
        painter.end()
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        image.save(buf, "JPG", 80)
        JpegData = buf.data()
        return JpegData

    def got_message(self):
        while self.osc_sock.hasPendingDatagrams():
            data, address, port = self.osc_sock.readDatagram(self.osc_sock.pendingDatagramSize())
            try:
                osc_address, typetags, args = decode_osc(data, 0, len(data))
            except ValueError, error:
                logger.exception(error)
            else:
                self.update(osc_address, args)


def main():
    arg_parser = ArgParser("ekgplotter")
    arg_parser.add_global_group()
    client_group = arg_parser.add_client_group()
    arg_parser.add_argument(client_group, '-x', "--http_host", default='::',
                            help='my host, defaults to "::"')
    arg_parser.add_argument(client_group, '-X', '--http_port', default=9000,
                            type=int, help='my port, defaults to 9000')
    arg_parser.add_chaosc_group()
    arg_parser.add_subscriber_group()
    args = arg_parser.finalize()

    args.http_host, args.http_port = resolve_host(args.http_host, args.http_port, args.address_family)
    args.chaosc_host, args.chaosc_port = resolve_host(args.chaosc_host, args.chaosc_port, args.address_family)

    window = EkgPlotWidget(args)
    logger.info("foooooooo")
    window.hide()
    #sys.excepthook = window.sigint_handler
    #signal.signal(signal.SIGTERM, window.sigterm_handler)
    qtapp.exec_()


if __name__ == '__main__':
    main()
