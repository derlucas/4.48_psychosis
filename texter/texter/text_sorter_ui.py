#!/usr/bin/env python
# coding=UTF-8
#
# Generated by pykdeuic4 from texter4.ui on Wed Apr 16 00:27:54 2014
#
# WARNING! All changes to this file will be lost.
from PyKDE4 import kdecore
from PyKDE4 import kdeui
from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_TextSorterDialog(object):
    def setupUi(self, TextSorterDialog):
        TextSorterDialog.setObjectName(_fromUtf8("TextSorterDialog"))
        TextSorterDialog.resize(662, 716)
        self.verticalLayout = QtGui.QVBoxLayout(TextSorterDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.text_list = QtGui.QListView(TextSorterDialog)
        self.text_list.setMinimumSize(QtCore.QSize(0, 576))
        self.text_list.setMaximumSize(QtCore.QSize(16777215, 576))
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(128, 125, 123))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        self.text_list.setPalette(palette)
        self.text_list.setObjectName(_fromUtf8("text_list"))
        self.horizontalLayout_2.addWidget(self.text_list)
        self.text_preview = KRichTextWidget(TextSorterDialog)
        self.text_preview.setMinimumSize(QtCore.QSize(0, 576))
        self.text_preview.setMaximumSize(QtCore.QSize(16777215, 576))
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        self.text_preview.setPalette(palette)
        self.text_preview.setReadOnly(True)
        self.text_preview.setObjectName(_fromUtf8("text_preview"))
        self.horizontalLayout_2.addWidget(self.text_preview)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.kbuttongroup = KButtonGroup(TextSorterDialog)
        self.kbuttongroup.setObjectName(_fromUtf8("kbuttongroup"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.kbuttongroup)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.move_down_button = KArrowButton(self.kbuttongroup)
        self.move_down_button.setProperty("arrowType", 2)
        self.move_down_button.setObjectName(_fromUtf8("move_down_button"))
        self.horizontalLayout.addWidget(self.move_down_button)
        self.move_up_button = KArrowButton(self.kbuttongroup)
        self.move_up_button.setObjectName(_fromUtf8("move_up_button"))
        self.horizontalLayout.addWidget(self.move_up_button)
        self.remove_button = KPushButton(self.kbuttongroup)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("edit-delete"))
        self.remove_button.setIcon(icon)
        self.remove_button.setObjectName(_fromUtf8("remove_button"))
        self.horizontalLayout.addWidget(self.remove_button)
        self.verticalLayout.addWidget(self.kbuttongroup)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(TextSorterDialog)
        QtCore.QMetaObject.connectSlotsByName(TextSorterDialog)

    def retranslateUi(self, TextSorterDialog):
        TextSorterDialog.setWindowTitle(kdecore.i18n(_fromUtf8("Form")))
        self.remove_button.setText(kdecore.i18n(_fromUtf8("Remove")))

from PyKDE4.kdeui import KButtonGroup, KArrowButton, KPushButton, KRichTextWidget