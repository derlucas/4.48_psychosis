#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of chaosc and psychosis
#
# chaosc/psychosis is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# chaosc/psychosis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with chaosc/psychosis.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2014 Stefan Kögl

from __future__ import absolute_import

import os
import os.path
import re
import sys

from datetime import datetime
from chaosc.argparser_groups import *
from chaosc.lib import logger, resolve_host
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QBuffer, QByteArray, QIODevice
from PyQt4.QtNetwork import QTcpServer, QTcpSocket

class MjpegStreamingServer(QTcpServer):

    def __init__(self, server_address, parent=None):
        super(MjpegStreamingServer, self).__init__(parent)
        self.server_address = server_address
        self.newConnection.connect(self.new_connection)
        self.widget = parent
        self.sockets = list()
        self.img_data = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.send_image)
        self.timer.start(80)
        self.stream_clients = list()
        self.get_regex = re.compile("^GET /(\w+?)\.(\w+?) HTTP/(\d+\.\d+)$")
        self.host_regex = re.compile("^Host: (\w+?):(\d+)$")
        self.html_map = dict()

    def handle_request(self):
        sock = self.sender()
        logger.info("handle_request: %s %d", sock.peerAddress(), sock.peerPort())
        sock_id = id(sock)
        if sock.state() in (QTcpSocket.UnconnectedState, QTcpSocket.ClosingState):
            logger.info("connection closed")
            self.sockets.remove(sock)
            sock.deleteLater()
            return

        client_data = str(sock.readAll())
        logger.info("request %r", client_data)
        line = client_data.split("\r\n")[0]
        logger.info("first line: %r", line)
        try:
            resource, ext, http_version = self.get_regex.match(line).groups()
            logger.info("resource=%r, ext=%r, http_version=%r", resource, ext, http_version)
        except AttributeError:
            try:
                host, port = self.host_regex.match(line).groups()
                logger.info("found host header %r %r", host, port)
                #return
                #sock.write("HTTP/1.1 501 Not Implemented\r\n")
                return
            except AttributeError:
                logger.info("no matching request - sending 404 not found")
                sock.write("HTTP/1.1 404 Not Found\r\n")
                return
        else:
            if ext == "ico":
                directory = os.path.dirname(os.path.abspath(__file__))
                data = open(os.path.join(directory, "favicon.ico"), "rb").read()
                sock.write(QByteArray('HTTP/1.1 200 Ok\r\nContent-Type: image/x-ico\r\n\r\n%s' % data))
            elif ext == "html":
                directory = os.path.dirname(os.path.abspath(__file__))
                data = open(os.path.join(directory, "index.html"), "rb").read() % sock_id
                self.html_map[sock_id] = None
                sock.write(QByteArray('HTTP/1.1 200 Ok\r\nContent-Type: text/html;encoding: utf-8\r\n\r\n%s' % data))
            elif ext == "mjpeg":
                try:
                    _, html_sock_id = resource.split("_", 1)
                    html_sock_id = int(html_sock_id)
                except ValueError:
                    html_sock_id = None

                if sock not in self.stream_clients:
                    logger.info("starting streaming...")
                    if html_sock_id is not None:
                        self.html_map[html_sock_id] = sock
                    self.stream_clients.append(sock)
                    sock.write(QByteArray('HTTP/1.1 200 Ok\r\nContent-Type: multipart/x-mixed-replace; boundary=--2342\r\n\r\n'))
            else:
                logger.error("request not found/handled - sending 404 not found")
                sock.write("HTTP/1.1 404 Not Found\r\n")

    def slot_remove_connection(self):
        try:
            sock = self.sender()
        except RuntimeError:
            return
        if sock.state() == QTcpSocket.UnconnectedState:
            self.__remove_connection(sock)

    def __remove_connection(self, sock):
        sock_id = id(sock)
        sock.disconnected.disconnect(self.slot_remove_connection)
        sock.close()
        sock.deleteLater()
        self.sockets.remove(sock)
        logger.info("connection removed: sock=%r, sock_id=%r", sock, sock_id)

        try:
            self.stream_clients.remove(sock)
        except ValueError:
            pass

        try:
            stream_client = self.html_map.pop(sock_id)
        except KeyError:
            logger.info("socket has no child socket")
        else:
            stream_client.close()
            try:
                self.stream_clients.remove(stream_client)
                logger.info("removed stream_client=%r", id(stream_client))
            except ValueError:
                pass

            try:
                self.sockets.remove(stream_client)
                logger.info("removed child sock_id=%r", id(stream_client))
            except ValueError:
                pass


    def send_image(self):
        if not self.stream_clients:
            return

        img_data = self.widget.render_image()
        len_data = len(img_data)
        array = QByteArray("--2342\r\nContent-Type: image/jpeg\r\nContent-length: %d\r\n\r\n%s\r\n\r\n\r\n" % (len_data, img_data))
        for sock in self.stream_clients:
            sock.write(array)

    def new_connection(self):
        while self.hasPendingConnections():
            sock = self.nextPendingConnection()
            logger.info("new connection=%r", id(sock))
            sock.readyRead.connect(self.handle_request)
            sock.disconnected.connect(self.slot_remove_connection)
            self.sockets.append(sock)

    def stop(self):
        self.stream_clients = list()
        self.sockets = list()
        self.html_map = dict()
        self.close()
