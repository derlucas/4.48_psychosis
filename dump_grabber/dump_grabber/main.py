#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys, os, random

from PyQt4 import QtCore, QtGui



from dump_grabber_ui import Ui_MainWindow
from PyKDE4.kdecore import ki18n, KCmdLineArgs, KAboutData
from PyKDE4.kdeui import KMainWindow, KApplication

appName     = "dump_grabber"
catalog     = "dump_grabber"
programName = ki18n("dump_grabber")
version     = "0.1"

aboutData = KAboutData(appName, catalog, programName, version)

KCmdLineArgs.init (sys.argv, aboutData)

app = KApplication()
class MainWindow(KMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
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
        self.font_metrics = QtGui.QFontMetrics(self.default_font)
        self.line_height = self.font_metrics.height()
        self.num_lines = 775/self.line_height
        
        self.graphics_scene.setFont(self.default_font)
        print "font", self.default_font.family(), self.default_font.pixelSize(), self.default_font.pointSize()
        self.brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        self.brush.setStyle(QtCore.Qt.SolidPattern)
        pos_y = 0
        for i in range(self.num_lines):
            text = self.graphics_scene.addSimpleText("osc address:/test/foo/bar      arguments:[%d]        types=[\"i\"]" % random.randint(0,255), self.default_font)
            text.setBrush(self.brush)
            text.setPos(0, i * self.line_height)
            pos_y += self.line_height

        self.graphics_view.show()

def main():
    window = MainWindow()
    window.show()
    app.exec_()


if ( __name__ == '__main__' ):
    main()
