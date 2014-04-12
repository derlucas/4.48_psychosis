# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'text_sorter.ui'
#
# Created: Sat Apr 12 14:47:10 2014
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

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

class Ui_text_sorter_dialog(object):
    def setupUi(self, text_sorter_dialog):
        text_sorter_dialog.setObjectName(_fromUtf8("text_sorter_dialog"))
        text_sorter_dialog.resize(612, 280)
        self.verticalLayout = QtGui.QVBoxLayout(text_sorter_dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.text_list = KEditListWidget(text_sorter_dialog)
        self.text_list.setObjectName(_fromUtf8("text_list"))
        self.horizontalLayout.addWidget(self.text_list)
        self.text_preview = KRichTextWidget(text_sorter_dialog)
        self.text_preview.setObjectName(_fromUtf8("text_preview"))
        self.horizontalLayout.addWidget(self.text_preview)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.buttonBox = QtGui.QDialogButtonBox(text_sorter_dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(text_sorter_dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), text_sorter_dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), text_sorter_dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(text_sorter_dialog)

    def retranslateUi(self, text_sorter_dialog):
        text_sorter_dialog.setWindowTitle(_translate("text_sorter_dialog", "Dialog", None))

from PyKDE4.kdeui import KEditListWidget, KRichTextWidget
