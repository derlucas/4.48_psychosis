#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys, os, random

from PyQt4 import QtCore, QtGui

from PyQt4.QtCore import QBuffer, QByteArray, QIODevice

from dump_grabber_ui import Ui_MainWindow
from PyKDE4.kdecore import ki18n, KCmdLineArgs, KAboutData
from PyKDE4.kdeui import KMainWindow, KApplication

from  datetime import datetime
import threading
import Queue
import traceback
import numpy as np
import string
import time
import random
import socket
import os.path
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn, ForkingMixIn
import select
import re

from collections import deque

from chaosc.argparser_groups import *
from chaosc.lib import resolve_host

try:
    from chaosc.c_osc_lib import OSCMessage, decode_osc
except ImportError as e:
    print(e)
    from chaosc.osc_lib import OSCMessage, decode_osc


appName     = "dump_grabber"
catalog     = "dump_grabber"
programName = ki18n("dump_grabber")
version     = "0.1"

aboutData = KAboutData(appName, catalog, programName, version)

KCmdLineArgs.init (sys.argv, aboutData)

app = KApplication()
class MainWindow(KMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, columns=3):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.graphics_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphics_view.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.graphics_view.setFrameStyle(QtGui.QFrame.NoFrame)
        self.graphics_scene = QtGui.QGraphicsScene(self)
        self.graphics_scene.setSceneRect(0,0, 775, 580)
        self.graphics_view.setScene(self.graphics_scene)
        self.default_font = QtGui.QFont("Monospace", 14)
        self.default_font.setStyleHint(QtGui.QFont.Monospace)
        self.default_font.setBold(True)
        self.blue_color = QtGui.QColor(47,147,235)
        self.font_metrics = QtGui.QFontMetrics(self.default_font)
        self.line_height = self.font_metrics.height()
        self.num_lines = 775/self.line_height

        self.graphics_scene.setFont(self.default_font)
        print "font", self.default_font.family(), self.default_font.pixelSize(), self.default_font.pointSize()
        self.brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        self.brush.setStyle(QtCore.Qt.SolidPattern)
        self.column_width = 775 / columns

        self.column_count = columns
        self.columns = list()
        for i in range(columns):
            column = list()
            for j in range(self.num_lines):
                text_item = self.graphics_scene.addSimpleText("", self.default_font)
                if column == 0:
                    text_item.setBrush(QtCore.Qt.red)
                elif column == 1:
                    text_item.setBrush(QtCore.Qt.green)
                elif column == 2:
                    text_item.setBrush(self.blue_color)
                text_item.setPos(j * self.line_height, i * self.column_width)
                column.append(text_item)
            self.columns.append(column)
        self.graphics_view.show()

    def add_text(self, column, text):
        text_item = self.graphics_scene.addSimpleText(text, self.default_font)
        if column == 0:
            text_item.setBrush(QtCore.Qt.red)
        elif column == 1:
            text_item.setBrush(QtCore.Qt.green)
        elif column == 2:
            text_item.setBrush(self.blue_color)
        old_item = self.columns[column].pop(0)
        self.graphics_scene.removeItem(old_item)
        self.columns[column].append(text_item)
        for ix, text_item in enumerate(self.columns[column]):
            text_item.setPos(column * self.column_width, ix * self.line_height)


    def render(self):
        image = QtGui.QImage(768, 576, QtGui.QImage.Format_ARGB32_Premultiplied)
        image.fill(QtCore.Qt.black)
        painter = QtGui.QPainter(image)
        #painter.setPen(QtCore.Qt.white)
        painter.setFont(self.default_font)
        self.graphics_view.render(painter, target=QtCore.QRectF(0,0,768,576),source=QtCore.QRect(0,0,768,576))
        return image


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

        print "%s: starting up osc receiver on '%s:%d'" % (
            datetime.now().strftime("%x %X"), self.client_address[0], self.client_address[1])

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
        msg.appendTypedArg(self.client_address[0], "s")
        msg.appendTypedArg(self.client_address[1], "i")
        msg.appendTypedArg(self.args.authenticate, "s")
        if self.args.subscriber_label is not None:
            msg.appendTypedArg(self.args.subscriber_label, "s")
        self.osc_sock.sendto(msg.encode_osc(), self.chaosc_address)


    def unsubscribe_me(self):
        if self.args.keep_subscribed:
            return

        print "%s: unsubscribing from '%s:%d'" % (datetime.now().strftime("%x %X"), self.chaosc_address[0], self.chaosc_address[1])
        msg = OSCMessage("/unsubscribe")
        msg.appendTypedArg(self.client_address[0], "s")
        msg.appendTypedArg(self.client_address[1], "i")
        msg.appendTypedArg(self.args.authenticate, "s")
        self.osc_sock.sendto(msg.encode_osc(), self.chaosc_address)

    def run(self):

        while self.running:
            try:
                reads, writes, errs = select.select([self.osc_sock], [], [], 0.01)
            except Exception, e:
                print "select error", e
                pass
            else:
                if reads:
                    try:
                        osc_input, address = self.osc_sock.recvfrom(8192)
                        osc_address, typetags, messages = decode_osc(osc_input, 0, len(osc_input))
                        queue.put_nowait((osc_address, messages))
                    except Exception, e:
                        print "recvfrom error", e
                else:
                    pass

        self.unsubscribe_me()
        print "OSCThread is going down"


queue = Queue.Queue()

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
                window = MainWindow()
                window.hide()

                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=--aaboundary")
                self.end_headers()

                event_loop = QtCore.QEventLoop()
                while 1:
                    event_loop.processEvents()
                    app.sendPostedEvents(None, 0)
                    while 1:
                        try:
                            osc_address, args = queue.get_nowait()
                        except Queue.Empty:
                            break
                        else:
                            if "merle" in osc_address:
                                window.add_text(0, "%s = %s" % (osc_address[7:], ", ".join([str(i) for i in args])))
                            elif "uwe" in osc_address:
                                window.add_text(1, "%s = %s" % (osc_address[5:], ", ".join([str(i) for i in args])))
                            elif "bjoern" in osc_address:
                                window.add_text(2, "%s = %s" % (osc_address[8:], ", ".join([str(i) for i in args])))

                    img = window.render()
                    buffer = QBuffer()
                    buffer.open(QIODevice.WriteOnly)
                    img.save(buffer, "JPG", 100)
                    img.save("/tmp/test.jpg", "JPG")

                    JpegData = buffer.data()
                    self.wfile.write("--aaboundary\r\nContent-Type: image/jpeg\r\nContent-length: %d\r\n\r\n%s\r\n\r\n\r\n" % (len(JpegData), JpegData))

                    JpegData = None
                    buffer = None
                    img = None
                    time.sleep(0.05)

            elif self.path.endswith(".jpeg"):
                directory = os.path.dirname(os.path.abspath(__file__))
                data = open(os.path.join(directory, self.path), "rb").read()
                self.send_response(200)
                self.send_header('Content-type','image/jpeg')
                self.end_headers()
                self.wfile.write(data)
            return
        except (KeyboardInterrupt, SystemError):
            print "queue size", queue.qsize()
            if hasattr(self, "thread") and self.thread is not None:
                self.thread.running = False
                self.thread.join()
                self.thread = None
        except IOError, e:
            print "ioerror", e, e[0]
            print dir(e)
            if e[0] in (32, 104):
                if hasattr(self, "thread") and self.thread is not None:
                    self.thread.running = False
                    self.thread.join()
                    self.thread = None
            else:
                print '-'*40
                print 'Exception happened during processing of request from'
                traceback.print_exc() # XXX But this goes to stderr!
                print '-'*40
                self.send_error(404,'File Not Found: %s' % self.path)


class JustAHTTPServer(HTTPServer):
    pass


def main():
    arg_parser = ArgParser("dump_grabber")
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
    print "%s: starting up http server on '%s:%d'" % (
        datetime.now().strftime("%x %X"), http_host, http_port)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()
        sys.exit(0)


if ( __name__ == '__main__' ):
    main()
