#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from operator import itemgetter

class TextModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        super(TextModel, self).__init__(parent)
        self.text_db = list()
        self.default_size = 32
        self.font = QtGui.QFont("monospace", self.default_size)
        self.font.setStyleHint(QtGui.QFont.TypeWriter)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.text_db)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def data(self, index, role):
        if not index.isValid() or \
            not 0 <= index.row() < self.rowCount():
            return QVariant()

        row = index.row()
        column = index.column()
        if role == QtCore.Qt.DisplayRole:
            print "data", row, column, row
            return QtCore.QVariant(self.text_db[row][column])
            #return "foo bar"

        return QtCore.QVariant()


    def headerData(self, section, orientation=QtCore.Qt.Horizontal, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if section == 0:
                return "Preview"
            else:
                return "Text"
        return QtCore.QVariant()

    def setData(self, index, value, role):
        if (not index.isValid() or
            not 0 <= index.row() < self.rowCount()):
            print "setData index not valid"
            return False

        print "setData", index.row(), index.column(), value, role

        if role == QtCore.Qt.EditRole:
            text = value.toString()
            if not text:
                return False
            else:
                self.text_db[index.row()][index.column()] = text
                return True
        else:
            return False

    def flags(self, index):
        if index.column() == 0:
            return QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
        else:
            return QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled


    def insertRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, row, row+count+1)
        for i in range(row, row+count):
            self.text_db.insert(parent.child(i).data())
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row+count+1)
        for i in range(row, row+count):
            self.text_db.pop(row)
        self.endRemoveRows()
        return True


    def text_by_preview(self, preview):
        for ix, (title, text) in enumerate(self.text_db):
            if title == preview:
                return ix, title, text
        return None

