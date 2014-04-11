#!/usr/bin/python
# -*- coding: utf-8 -*-

import PyQt4.uic
from PyQt4 import QtCore, QtGui
from PyKDE4.kdeui import KActionCollection, KRichTextWidget

MainWindowForm, MainWindowBase = PyQt4.uic.loadUiType('texter.ui')

from operator import itemgetter
import cPickle

class MainWindow(MainWindowBase, MainWindowForm):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)


        # setup the ui
        self.setupUi(self)
        #self.show_public_text.setRichTextSupport(KRichTextWidget.RichTextSupport(0xffffffff))
        self.edit_private_text.setRichTextSupport(KRichTextWidget.RichTextSupport(0xffffffff))
        self.edit_action_collection = KActionCollection(self)
        self.edit_private_text.createActions(self.edit_action_collection)
        for action in self.edit_action_collection.actions():
            self.toolBar.addAction(action)

        self.current_text = None
        self.current_title = None
        self.current_index = None
        self.is_published = False

        self.tabWidget.currentChanged.connect(self.slot_toggleToolbox)
        self.add_button.clicked.connect(self.slot_addText)
        self.save_button.clicked.connect(self.slot_save)
        self.publish_button.toggled.connect(self.slot_toggle_publish)
        self.remove_item_button.clicked.connect(self.slot_removeItem)
        self.edit_item_selection.activated.connect(self.slot_editLoadItem)
        self.item_list.currentRowChanged.connect(self.slot_showLoadItem)
        self.auto_publish_checkbox.toggled.connect(self.slot_toggle_publish)

        self.items = dict()
        self.slot_load()
        self.next_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Space))
        self.next_button.clicked.connect(self.slot_next_item)

        self.previous_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Backspace))
        self.previous_button.clicked.connect(self.slot_previous_item)


    def slot_next_item(self):
        print "slot_next_item"
        print "current_title", self.current_title, self.current_text
        index = (self.item_list.currentRow() + 1) % self.item_list.count()
        self.item_list.setCurrentRow(index)
        self.edit_item_selection.setCurrentIndex(index)
        self.slot_editLoadItem(index)
        self.slot_showLoadItem(index)

    def slot_previous_item(self):
        print "slot_previous_item"
        print "current_title", self.current_title, self.current_text
        index = (self.item_list.currentRow() - 1) % self.item_list.count()
        self.item_list.setCurrentRow(index)
        self.edit_item_selection.setCurrentIndex(index)
        self.slot_editLoadItem(index)
        self.slot_showLoadItem(index)

    def slot_toggleToolbox(self, index):
        print "slot_toggleToolbox"
        print "current_title", self.current_title, self.current_text
        if index == 0:
            self.toolBar.setEnabled(True)
        else:
            self.toolBar.setEnabled(False)

    def slot_publish(self):
        #QPropertyAnimation animation(self.public_text.palette(), "geometry");
        #animation.setDuration(10000);
        #animation.setStartValue(QRect(0, 0, 100, 30));
        #animation.setEndValue(QRect(250, 250, 100, 30));
        #animation.start();
        print "slot_publish"
        print "current_title", self.current_title, self.current_text
        self.show_public_text.setTextOrHtml(self.current_text)
        self.is_published = True

    def slot_toggle_publish(self, state=None):
        #QPropertyAnimation animation(self.public_text.palette(), "geometry");
        #animation.setDuration(10000);
        #animation.setStartValue(QRect(0, 0, 100, 30));
        #animation.setEndValue(QRect(250, 250, 100, 30));
        #animation.start();
        print "slot_toggle_publish", state
        print "current_title", self.current_title, self.current_text

        if state:
            self.slot_publish()
        else:
            self.slot_clear()

    def slot_clear(self):
        print "slot_clear"
        print "current_title", self.current_title, self.current_text

        self.show_public_text.clear()
        self.is_published = False

    def slot_removeItem(self):
        text = self.edit_item_selection.currentText()
        index = self.edit_item_selection.currentIndex()
        title = text.split(": ")[1]
        del self.items[title]
        self.edit_item_selection.removeItem(index)
        self.item_list.removeItemWidget(self.item_list.item(index))
        new_index = self.edit_item_selection.currentIndex()
        if new_index != -1:
            self.slot_editLoadItem()
        else:
            self.item_title.clear()
            self.item_position_input.setValue(0)


    def slot_editLoadItem(self, index):
        print "slot_editLoadItem", index
        itemText = self.edit_item_selection.itemText(index)
        position, title = itemText.split(": ", 1)
        text, position = self.items[title]
        self.edit_private_text.setTextOrHtml(text)
        self.item_title.setText(title)
        self.item_position_input.setValue(position)

    def slot_showLoadItem(self, index):
        public_rect = self.show_public_text.geometry()
        global_rect = QtCore.QRect(self.mapToGlobal(public_rect.topLeft()), self.mapToGlobal(public_rect.bottomRight()))
        print "slot_showLoadItem", global_rect, index
        print "current_title", self.current_title, self.current_text
        item = self.item_list.item(index)
        print "item", item
        if item is None:
            return
        self.current_title = item.text()
        self.current_text, self.current_index = self.items[self.current_title]
        print "current_title", self.current_title, self.current_text
        if self.auto_publish_checkbox.isChecked():
            self.show_public_text.setHtml(self.current_text)

    def title_by_index(self, ix):
        for title, (text, index) in self.items.iteritems():
            if index == ix:
                return title
        return None

    def slot_changeItem(self, old_title):
        print "slot_changeItem"
        text, index = self.items.pop(old_title)
        new_text = self.edit_private_text.textOrHtml()
        new_title = self.item_title.text()
        self.items[new_title] = (new_text, index)
        self.show_public_text.setTextOrHtml(new_text)
        self.item_title.setText(new_title)
        self.edit_item_selection.setItemText(index, "%d: %s" % (index, new_title))
        self.item_list.item(index).setText(new_title)

    def slot_addText(self):
        print "slot add"
        index = self.item_position_input.value()
        if index - self.item_list.count() > 1:
            old_title = self.edit_item_selection.currentText().split(": ")[1]
            self.item_title.setText(old_title)
            text, index = self.items[old_title]
            self.edit_private_text.setTextOrHtml(text)
            self.item_position_input.setValue(index)
            return
        old_title = self.title_by_index(index)
        if old_title is not None:
            self.slot_changeItem(old_title)
            return

        title = self.item_title.text()
        text = self.edit_private_text.textOrHtml()
        self.items[title] = (text, index)
        self.edit_item_selection.insertItem(index, "%d: %s" % (index, title))
        self.item_list.insertItem(index, title)
        self.edit_item_selection.setCurrentIndex(index)
        self.item_list.setCurrentRow(index)

    def slot_save(self):
        cPickle.dump(self.items, open("448_texter.db", "w"), cPickle.HIGHEST_PROTOCOL)

    def slot_load(self):
        try:
            self.items = cPickle.load(open("448_texter.db"))
        except Exception, e:
            print e

        data = list()
        for title, (text, index) in self.items.iteritems():
            data.append((title, text, index))

        data = sorted(data, key=itemgetter(2))
        for title, text, index in data:
            self.edit_item_selection.addItem("%d: %s" % (index, title))
            self.item_list.addItem(title)

        self.edit_item_selection.setCurrentIndex(0)
        self.item_list.setCurrentRow(0)
        self.current_title, self.current_text, self.current_index = data[0]

        self.edit_private_text.setTextOrHtml(self.current_text)
        self.item_position_input.setValue(self.current_index)
        self.item_title.setText(self.current_title)



if ( __name__ == '__main__' ):
    app = None
    if ( not app ):
        app = QtGui.QApplication([])

    window = MainWindow()
    window.show()

    if ( app ):
        app.exec_()
