#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of chaosc/psylib package
#
# chaosc/psylib is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# chaosc/psylib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with chaosc/psylib.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2014 Stefan Kögl

from __future__ import absolute_import

import sys
import traceback

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QBuffer, QByteArray
from PyQt4.QtNetwork import QUdpSocket, QHostAddress


from chaosc.lib import logger

try:
    from chaosc.c_osc_lib import OSCMessage, decode_osc
except ImportError as e:
    from chaosc.osc_lib import OSCMessage, decode_osc


class PsyQtClientBase(QtCore.QObject):

    def __init__(self):
        super(PsyQtClientBase, self).__init__()
        # periodically trap into python interpreter domain to catch signals etc
        timer = QtCore.QTimer()
        timer.start(2000)
        timer.timeout.connect(lambda: None)

    def sigint_handler(self, ex_cls, ex, traceback):
        """Handler for the SIGINT signal."""
        if ex_cls == KeyboardInterrupt:
            logger.info("found KeyboardInterrupt")
            QtGui.QApplication.exit()
        else:
            logger.critical(''.join(traceback.format_tb(tb)))
            logger.critical('{0}: {1}'.format(ex_cls, ex))

class PsyQtChaoscClientBase(PsyQtClientBase):

    def __init__(self):
        super(PsyQtChaoscClientBase, self).__init__()
        self.osc_sock = QUdpSocket(self)
        logger.info("osc bind localhost %d", self.args.client_port)
        self.osc_sock.bind(QHostAddress(self.args.client_host), self.args.client_port)
        self.osc_sock.readyRead.connect(self.got_message)
        self.osc_sock.error.connect(self.handle_osc_error)
        self.subscribe()

    def sigint_handler(self, ex_cls, ex, tb):
        """Handler for the SIGINT signal."""
        logger.info("sigint_handler")
        if ex_cls == KeyboardInterrupt:
            logger.info("found KeyboardInterrupt")
            self.unsubscribe()
            QtGui.QApplication.exit()
        else:
            logger.critical(''.join(traceback.format_tb(tb)))
            logger.critical('{0}: {1}'.format(ex_cls, ex))

    def sigterm_handler(self, *args):
        logger.info("sigterm_handler")
        self.unsubscribe()
        QtGui.QApplication.exit()

    def subscribe(self):
        logger.info("subscribe")
        msg = OSCMessage("/subscribe")
        logger.info(self.args.client_host)
        msg.appendTypedArg(self.args.client_host, "s")
        msg.appendTypedArg(self.args.client_port, "i")
        msg.appendTypedArg(self.args.authenticate, "s")
        if self.args.subscriber_label is not None:
            msg.appendTypedArg(self.args.subscriber_label, "s")
        self.osc_sock.writeDatagram(QByteArray(msg.encode_osc()), QHostAddress(self.args.chaosc_host), self.args.chaosc_port)

    def unsubscribe(self):
        logger.info("unsubscribe")
        msg = OSCMessage("/unsubscribe")
        msg.appendTypedArg(self.args.client_host, "s")
        msg.appendTypedArg(self.args.client_port, "i")
        msg.appendTypedArg(self.args.authenticate, "s")
        self.osc_sock.writeDatagram(QByteArray(msg.encode_osc()), QHostAddress(self.args.chaosc_host), self.args.chaosc_port)

    def handle_osc_error(self, error):
        logger.info("osc socket error %d", error)

    def closeEvent(self, event):
        logger.info("closeEvent", event)
        self.unsubscribe()
        event.accept()
