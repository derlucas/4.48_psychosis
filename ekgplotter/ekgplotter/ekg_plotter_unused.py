import numpy as np
import string,cgi,time, random, socket
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn, ForkingMixIn
import select
import re

from collections import deque

from PyQt4.QtCore import QBuffer, QByteArray, QIODevice, QThread, QObject
from PyQt4 import QtGui
from PyQt4 import QtCore
import pyqtgraph as pg

from pyqtgraph.widgets.PlotWidget import PlotWidget


try:
    from chaosc.c_osc_lib import decode_osc
except ImportError as e:
    print(e)
    from chaosc.osc_lib import decode_osc

QAPP = None

def mkQApp():
    if QtGui.QApplication.instance() is None:
        global QAPP
        QAPP = QtGui.QApplication([])


class PlotWindow(PlotWidget):
    def __init__(self, title=None, **kargs):
        mkQApp()
        self.win = QtGui.QMainWindow()
        PlotWidget.__init__(self, **kargs)
        self.win.setCentralWidget(self)
        for m in ['resize']:
            setattr(self, m, getattr(self.win, m))
        if title is not None:
            self.win.setWindowTitle(title)


class WorkThread(QThread):
    osc_received = QtCore.pyqtSignal(str, int, name='osc_received')

    def __init__(self):
        QThread.__init__(self)
        self.osc_sock = socket.socket(2, 2, 17)
        self.osc_sock.setblocking(0)
        self.osc_sock.setsockopt(socket.SOL_SOCKET,
            socket.SO_RCVBUF, 4096 * 8)
        self.osc_sock.bind(("", 10000))


    def __del__(self):
        self.wait()

    def run(self):
        while 1:
            reads, writes, errs = select.select([self.osc_sock], [], [], 0.01)
            if reads:
                osc_input = reads[0].recv(4096)
                osc_address, typetags, args = decode_osc(osc_input, 0, len(osc_input))
                print "signal", osc_address, args[0]
                self.osc_received.emit(osc_address, args[0])


class MyHandler(QtCore.QObject, BaseHTTPRequestHandler):

    def __init__(self, request, client_address, parent):
        self.plot_data1 = deque([0] * 100)
        self.plot_data2 = deque([254/3] * 100)
        self.plot_data3 = deque([254/3*2] * 100)
        self.is_item1 = True
        self.is_item2 = True
        self.is_item3 = True
        QtCore.QObject.__init__(self)
        BaseHTTPRequestHandler.__init__(self, request, client_address, parent)

    @QtCore.pyqtSlot('QString', int, name="receive_osc")
    def receive_osc(self, osc_address, value):
        print "change", osc_address, value
        if osc_address == "/bjoern/ekg":
            self.plot_data1.appendleft(args[0] / 3)
            self.plot_data1.pop()
        elif osc_address == "/merle/ekg":
            self.plot_data2.appendleft(args[0] / 3 + 254/3)
            self.plot_data2.pop()
        elif osc_address == "/uwe/ekg":
            self.plot_data3.appendleft(args[0] / 3 + 254/3*2)
            self.plot_data3.pop()
        elif osc_address == "/plot/uwe":
            if value == 1 and self.is_item3 == False:
                self.plt.addItem(self.plotItem3)
            elif value == 0 and self.is_item3 == True:
                self.plt.removeItem(self.plotItem3)
        elif osc_address == "/plot/merle":
            if value == 1 and self.is_item2 == False:
                self.plt.addItem(self.plotItem2)
            elif value == 0 and self.is_item2 == True:
                self.plt.removeItem(self.plotItem2)
        elif osc_address == "/plot/bjoern":
            if value == 1 and self.is_item1 == False:
                self.plt.addItem(self.plotItem1)
            elif value == 0 and self.is_item1 == True:
                self.plt.removeItem(self.plotItem1)

    def do_GET(self):
        print "get"
        global plotValues
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
                return
            if self.path.endswith(".mjpeg"):
                self.thread = WorkThread()
                #self.thread.osc_received.connect(self.change)
                #self.connect(self.thread, thread.osc_received, self.change)
                self.thread.osc_received.connect(self.receive_osc)
                self.thread.start()

                self.send_response(200)

                self.plt = plt = PlotWindow(title="EKG", name="Merle")
                plt.addLegend()
                #plt = pg.plot(pen=(0, 3*1.3))
                plt.resize(1280, 720)
                self.plotItem1 = plotItem1 = pg.PlotCurveItem(pen=pg.mkPen('r', width=4), name="bjoern")
                self.plotItem2 = plotItem2 = pg.PlotCurveItem(pen=pg.mkPen('g', width=4), name="merle")
                self.plotItem3 = plotItem3 = pg.PlotCurveItem(pen=pg.mkPen('b', width=4), name="uwe")
                plotItem1.setPos(0, 0*6)
                plotItem2.setPos(0, 1*6)
                plotItem3.setPos(0, 2*6)
                plt.addItem(plotItem1)
                plt.addItem(plotItem2)
                plt.addItem(plotItem3)

                plt.setLabel('left', "EKG")
                plt.setLabel('bottom', "Time")
                plt.showGrid(True, True)
                ba = plt.getAxis("bottom")
                bl = plt.getAxis("left")
                ba.setTicks([])
                bl.setTicks([])
                plt.setYRange(0, 254)
                #print type(plt)
                self.wfile.write("Content-Type: multipart/x-mixed-replace; boundary=--aaboundary")
                self.wfile.write("\r\n\r\n")

                last = time.time()
                now = last

                while 1:
                    plotItem1.setData(y=np.array(self.plot_data1), clear=True)
                    plotItem2.setData(y=np.array(self.plot_data2), clear=True)
                    plotItem3.setData(y=np.array(self.plot_data3), clear=True)
                    #item = plt.plot(plot_data1, pen=(0, 3*1.3), clear=True)

                    exporter = pg.exporters.ImageExporter.ImageExporter(plt.plotItem)
                    exporter.parameters()['width'] = 1280
                    #exporter.parameters()['height'] = 720
                    name = 'tmpfile'
                    img = exporter.export(name, True)
                    buffer = QBuffer()
                    buffer.open(QIODevice.ReadWrite)
                    img.save(buffer, "JPG", 100)
                    JpegData = buffer.data()
                    self.wfile.write("--aaboundary\r\n")
                    self.wfile.write("Content-Type: image/jpeg\r\n")
                    self.wfile.write("Content-length: %d\r\n\r\n" % len(JpegData))
                    self.wfile.write(JpegData)
                    self.wfile.write("\r\n\r\n\r\n")
                    now = time.time()
                    dur = now - last
                    #print dur
                    wait = 0.04 - dur
                    if wait > 0:
                        time.sleep(wait)
                    last = now
                return
            if self.path.endswith(".jpeg"):
                f = open(curdir + sep + self.path)
                self.send_response(200)
                self.send_header('Content-type','image/jpeg')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            return
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)


class ThreadedHTTPServer(HTTPServer, ForkingMixIn):
    """Handle requests in a separate process."""

def main():
    try:
        server = ThreadedHTTPServer(('0.0.0.0', 9000), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main()
