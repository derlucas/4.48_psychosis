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

import os.path
import re

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QPixmap, QMainWindow
from PyQt4.QtCore import QIODevice, QBuffer, QByteArray
from PyQt4.QtNetwork import QUdpSocket, QHostAddress
import numpy as np
import pyqtgraph as pg
from pyqtgraph.widgets.PlotWidget import PlotWidget
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
from pyqtgraph.graphicsItems.ScatterPlotItem import ScatterPlotItem
from chaosc.argparser_groups import ArgParser
from chaosc.lib import logger, resolve_host


try:
    from chaosc.c_osc_lib import OSCMessage, decode_osc
except ImportError as e:
    from chaosc.osc_lib import OSCMessage, decode_osc

qtapp = QtGui.QApplication([])


def get_steps(pulse, delta_ms):
    beat_length = 60000. / pulse
    steps_pre = int(beat_length / delta_ms) + 1
    used_sleep_time = beat_length / steps_pre
    steps = int(beat_length / used_sleep_time)
    return steps, used_sleep_time


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


class EkgPlotWidget(QMainWindow):
    def __init__(self, args, parent=None):
        self.args = args
        QMainWindow.__init__(self, parent)
        self.mcount = 0

        self.osc_sock = QUdpSocket(self)
        logger.info("osc bind localhost %d", self.args.client_port)
        self.osc_sock.bind(QHostAddress(self.args.client_host), self.args.client_port)
        self.osc_sock.readyRead.connect(self.got_message)
        self.osc_sock.error.connect(self.handle_osc_error)
        self.subscribe()

        self.plot_widget = PlotWidget()
        self.setCentralWidget(self.plot_widget)
        self.resize(args.client_width, args.client_height)
        colors = ["r", "g", "b"]
        self.active_actors = list()
        self.actors = dict()
        self.max_value = 255
        actor_names = ["merle", "uwe", "bjoern"]
        self.max_actors = len(actor_names)
        self.actor_height = self.max_value / self.max_actors
        self.fps = 12.5
        self.num_data = 640
        self.plot_widget.showGrid(False, False)
        self.plot_widget.setYRange(0, 255)
        self.plot_widget.setXRange(0, self.num_data)
        self.plot_widget.resize(args.client_width, args.client_height)

        bottom_axis = self.plot_widget.getAxis("bottom")
        left_axis = self.plot_widget.getAxis("left")
        bottom_axis.setTicks([])
        left_axis.setTicks([])
        bottom_axis.hide()
        left_axis.hide()

        for ix, (actor_name, color) in enumerate(zip(actor_names, colors)):
            self.add_actor(actor_name, self.num_data, color, ix, self.max_actors, self.actor_height)

        self.set_positions()
        self.ekg_regex = re.compile("^/(.*?)/ekg$")
        self.heartbeat_regex = re.compile("^/(.*?)/heartbeat$")

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.render_image)
        self.timer.start(50)


    def subscribe(self):
        logger.info("subscribe")
        msg = OSCMessage("/subscribe")
        msg.appendTypedArg(self.args.client_host, "s")
        msg.appendTypedArg(self.args.client_port, "i")
        msg.appendTypedArg(self.args.authenticate, "s")
        if self.args.subscriber_label is not None:
            msg.appendTypedArg(self.args.subscriber_label, "s")
        self.osc_sock.writeDatagram(QByteArray(msg.encode_osc()), QHostAddress(self.args.chaosc_host),
                                    self.args.chaosc_port)

    def unsubscribe(self):
        logger.info("unsubscribe")
        msg = OSCMessage("/unsubscribe")
        msg.appendTypedArg(self.args.client_host, "s")
        msg.appendTypedArg(self.args.client_port, "i")
        msg.appendTypedArg(self.args.authenticate, "s")
        self.osc_sock.writeDatagram(QByteArray(msg.encode_osc()), QHostAddress(self.args.chaosc_host),
                                    self.args.chaosc_port)

    def handle_osc_error(self, error):
        logger.info("osc socket error %d", error)

    def closeEvent(self, event):
        logger.info("closeEvent %r", event)
        self.unsubscribe()
        event.accept()

    def pubdir(self):
        return os.path.dirname(os.path.abspath(__file__))

    def add_actor(self, actor_name, num_data, color, ix, max_actors, actor_height):
        actor_obj = Actor(actor_name, num_data, color, ix, max_actors, actor_height)
        self.actors[actor_name] = actor_obj
        self.plot_widget.addItem(actor_obj.plotItem)
        self.plot_widget.addItem(actor_obj.plotPoint)
        self.active_actors.append(actor_obj)

    def set_positions(self):
        for ix, actor_obj in enumerate(self.active_actors):
            actor_obj.plotItem.setPos(0, ix * 2)
            actor_obj.plotPoint.setPos(0, ix * 2)

    def active_actor_count(self):
        return self.max_actors

    def update(self, osc_address, args):
        res = self.ekg_regex.match(osc_address)
        if res:
            self.mcount += 1
            actor_name = res.group(1)
            actor_obj = self.actors[actor_name]
            actor_obj.add_value(args[0])
            # logger.info("actor: %r, %r", actor_name, args)

    def render_image(self):
        for actor_obj in self.active_actors:
            actor_obj.add_value(actor_obj.osci.next())
            actor_obj.render()

    @QtCore.pyqtSlot()
    def render_image(self):
        for actor_obj in self.active_actors:
            actor_obj.render()
        print self.mcount

    def got_message(self):
        while self.osc_sock.hasPendingDatagrams():
            data, address, port = self.osc_sock.readDatagram(self.osc_sock.pendingDatagramSize())
            try:
                osc_address, typetags, args = decode_osc(data, 0, len(data))
                self.update(osc_address, args)
            except ValueError, error:
                logger.exception(error)


def main():
    arg_parser = ArgParser("ekgplotter")
    arg_parser.add_global_group()
    arg_parser.add_chaosc_group()
    arg_parser.add_subscriber_group()
    client_group = arg_parser.add_client_group()
    arg_parser.add_argument(client_group, '-W', "--client_width", type=int, default=640,
                      help='my host, defaults to "::"')
    arg_parser.add_argument(client_group, '-B', "--client_height", type=int, default=480,
                      help='my port, defaults to 8000')
    args = arg_parser.finalize()

    args.chaosc_host, args.chaosc_port = resolve_host(args.chaosc_host, args.chaosc_port, args.address_family)

    window = EkgPlotWidget(args)
    logger.info("foooooooo")
    window.show()
    # sys.excepthook = window.sigint_handler
    # signal.signal(signal.SIGTERM, window.sigterm_handler)
    qtapp.exec_()


if __name__ == '__main__':
    main()
