#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of chaosc and psychosis
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

from __future__ import absolute_import

import os
import os.path
import re
import signal
import sys
from collections import deque

from chaosc.argparser_groups import ArgParser
from chaosc.lib import logger, resolve_host
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QBuffer, QByteArray, QIODevice
from PyQt4.QtGui import QPixmap, QPainter
from PyQt4.QtNetwork import QHostAddress

from dump_grabber.dump_grabber_ui import Ui_MainWindow
from psylib.mjpeg_streaming_server import (MjpegStreamingServer,
                                           MjpegStreamingConsumerInterface)
from psylib.psyqt_base import PsyQtChaoscClientBase

try:
    from chaosc.c_osc_lib import OSCMessage, decode_osc
except ImportError:
    from chaosc.osc_lib import OSCMessage, decode_osc

QTAPP = QtGui.QApplication([])

class ExclusiveTextStorage(object):
    """Stores the text representation of per actor osc messages"""

    def __init__(self, columns, default_font, column_width, line_height, scene):
        self.column_count = columns
        self.colors = (
            QtCore.Qt.red, QtCore.Qt.green, QtGui.QColor(46, 100, 254))
        self.lines = deque()
        self.default_font = default_font
        self.column_width = column_width
        self.line_height = line_height
        self.graphics_scene = scene
        self.num_lines, self.offset = divmod(576, self.line_height)
        self.data = deque()

    def init_columns(self):
        color = self.colors[0]
        for line_index in range(self.num_lines):
            text_item = self.graphics_scene.addSimpleText("", self.default_font)
            text_item.setBrush(color)
            text_item.setPos(0, line_index * self.line_height)
            self.lines.append(text_item)

    def __add_text(self, column, text):
        text_item = self.graphics_scene.addSimpleText(text, self.default_font)
        text_item.setX(column * self.column_width)
        text_item.setBrush(self.colors[column])
        old_item = self.lines.popleft()
        self.graphics_scene.removeItem(old_item)
        self.lines.append(text_item)

    def finish(self):
        for column, text in self.data:
            self.__add_text(column, text)
        self.data.clear()

        for text_index, text_item in enumerate(self.lines):
            text_item.setY(text_index * self.line_height)

    def add_text(self, column, text):
        self.data.append((column, text))


class MainWindow(QtGui.QMainWindow, Ui_MainWindow,
                 MjpegStreamingConsumerInterface, PsyQtChaoscClientBase):

    """This app receives per actor osc messages and provides an mjpeg stream
    with colored text representation arranged in columns"""

    def __init__(self, args, parent=None):
        self.args = args
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.http_server = MjpegStreamingServer(
            (args.http_host, args.http_port), self)
        self.http_server.listen(port=args.http_port)
        self.graphics_view.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.graphics_view.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.graphics_view.setFrameStyle(QtGui.QFrame.NoFrame)
        self.graphics_scene = QtGui.QGraphicsScene(self)
        self.graphics_scene.setSceneRect(0, 0, 775, 580)
        self.graphics_view.setScene(self.graphics_scene)
        self.default_font = QtGui.QFont("Monospace", 14)
        self.default_font.setStyleHint(QtGui.QFont.Monospace)
        self.default_font.setBold(True)
        self.graphics_scene.setFont(self.default_font)
        self.font_metrics = QtGui.QFontMetrics(self.default_font)
        self.line_height = self.font_metrics.height()
        columns = 3
        self.column_width = 775 / columns
        self.text_storage = ExclusiveTextStorage(columns, self.default_font,
                                                 self.column_width,
                                                 self.line_height,
                                                 self.graphics_scene)
        self.text_storage.init_columns()
        self.regex = re.compile("^/(uwe|merle|bjoern)/(.*?)$")

    def pubdir(self):
        return os.path.dirname(os.path.abspath(__file__))

    def closeEvent(self, event):
        msg = OSCMessage("/unsubscribe")
        msg.appendTypedArg("localhost", "s")
        msg.appendTypedArg(self.args.client_port, "i")
        msg.appendTypedArg(self.args.authenticate, "s")
        self.osc_sock.writeDatagram(
            QByteArray(msg.encode_osc()), QHostAddress("127.0.0.1"), 7110)

    def handle_osc_error(self, error):
        logger.info("osc socket error %d", error)

    def add_text(self, column, text):
        self.text_storage.add_text(column, text)

    def render_image(self):
        self.text_storage.finish()
        image = QPixmap(768, 576)
        image.fill(QtCore.Qt.black)
        painter = QPainter(image)
        painter.setRenderHints(QPainter.RenderHint(
            QPainter.Antialiasing | QPainter.TextAntialiasing), True)
        painter.setFont(self.default_font)
        self.graphics_view.render(
            painter, target=QtCore.QRectF(0, 0, 768, 576),
            source=QtCore.QRect(0, 0, 768, 576))
        painter.end()
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        image.save(buf, "JPG", 100)
        image_data = buf.data()
        return image_data

    def got_message(self):
        while self.osc_sock.hasPendingDatagrams():
            data, address, port = self.osc_sock.readDatagram(
                self.osc_sock.pendingDatagramSize())
            try:
                osc_address, typetags, args = decode_osc(data, 0, len(data))
            except ValueError:
                return
            try:
                actor, text = self.regex.match(osc_address).groups()
            except AttributeError:
                pass
            else:
                if actor == "merle":
                    self.add_text(0, "%s = %s" % (
                        text, ", ".join([str(i) for i in args])))
                elif actor == "uwe":
                    self.add_text(1, "%s = %s" % (
                        text, ", ".join([str(i) for i in args])))
                elif actor == "bjoern":
                    self.add_text(2, "%s = %s" % (
                        text, ", ".join([str(i) for i in args])))
        return True


def main():
    arg_parser = ArgParser("dump_grabber")
    arg_parser.add_global_group()
    client_group = arg_parser.add_client_group()
    arg_parser.add_argument(client_group, '-x', "--http_host", default="::",
                            help='my host, defaults to "::"')
    arg_parser.add_argument(client_group, '-X', "--http_port", default=9001,
                            type=int, help='my port, defaults to 9001')
    arg_parser.add_chaosc_group()
    arg_parser.add_subscriber_group()
    args = arg_parser.finalize()

    args.http_host, args.http_port = resolve_host(
        args.http_host, args.http_port, args.address_family)
    args.chaosc_host, args.chaosc_port = resolve_host(
        args.chaosc_host, args.chaosc_port, args.address_family)

    window = MainWindow(args)
    sys.excepthook = window.sigint_handler
    signal.signal(signal.SIGTERM, window.sigterm_handler)
    QTAPP.exec_()


if __name__ == '__main__':
    main()
