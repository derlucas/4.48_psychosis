#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path

import PyQt4.uic
from PyQt4 import QtCore, QtGui
from PyKDE4.kdeui import KActionCollection, KRichTextWidget

from texter_ui import Ui_MainWindow
from text_sorter_ui import Ui_text_sorter_dialog

from operator import itemgetter
import cPickle

app = QtGui.QApplication([])


class TextSorterDialog(QtGui.QDialog, Ui_text_sorter_dialog):
    def __init__(self, parent = None):
        super(TextSorterDialog, self).__init__(parent)

        # setup the ui
        self.setupUi(self)
        self.fill_list()
        
        self.text_list.listView().clicked.connect(self.slot_show_text)
        self.accepted.connect(self.slot_saveToDb)
    
    def fill_list(self):
        for preview, text in self.parent().text_db:
            self.text_list.insertItem(preview)
    
    def slot_text_up(self):
        pass
    
    def slot_text_down(self):
        pass
    
    def slot_show_text(self, model_index):
        self.text_preview.setTextOrHtml(self.parent().text_db[model_index.row()][1])
    
    def slot_saveToDb(self):
        data = list()
        def findInDb(title):
            for preview, text in self.parent().text_db:
                if title == preview:
                    return text
            return None
                
        for i in self.text_list.items():
            text = findInDb(i)
            data.append((i, text))
        self.parent().text_db = data   
        print self.parent().text_db


class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)

        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)

        # setup the ui
        self.setupUi(self)
        self.font = QtGui.QFont("monospace", 22)
        self.font.setStyleHint(QtGui.QFont.TypeWriter)
        self.preview_text.document().setDefaultFont(self.font)

        self.preview_text.setRichTextSupport(KRichTextWidget.RichTextSupport(0xffffffff))
        self.preview_action_collection = KActionCollection(self)
        self.preview_text.createActions(self.preview_action_collection)
        self.preview_toolbar = QtGui.QToolBar("preview editor toolbar", self)
        self.preview_toolbar.setAllowedAreas(QtCore.Qt.BottomToolBarArea)
        self.preview_toolbar.setMovable(False)
        self.preview_toolbar.setFloatable(False)
        #self.addToolBar(QtCore.Qt.BottomToolBarArea, self.preview_toolbar)
        for action in self.preview_action_collection.actions():
            self.preview_toolbar.addAction(action)

        self.live_text.setRichTextSupport(KRichTextWidget.RichTextSupport(0xffffffff))
        self.live_text.document().setDefaultFont(self.font)
        self.live_action_collection = KActionCollection(self)
        self.live_text.createActions(self.live_action_collection)
        self.live_toolbar = QtGui.QToolBar("live editor toolbar", self)
        self.live_toolbar.setAllowedAreas(QtCore.Qt.BottomToolBarArea)
        self.live_toolbar.setMovable(False)
        self.live_toolbar.setFloatable(False)
        #self.addToolBar(QtCore.Qt.RightToolBarArea, self.live_toolbar)
        for action in self.live_action_collection.actions():
            self.live_toolbar.addAction(action)

        self.show()

        self.is_published = False
        self.current = 0

        #self.add_button.clicked.connect(self.slot_addText)
        #self.save_button.clicked.connect(self.slot_save)
        self.publish_button.clicked.connect(self.slot_publish)
        self.clear_live_button.clicked.connect(self.slot_clear_live)
        self.clear_preview_button.clicked.connect(self.slot_clear_preview)
        #self.remove_item_button.clicked.connect(self.slot_removeItem)
        #self.edit_item_selection.activated.connect(self.slot_editLoadItem)
        #self.auto_publish_checkbox.clicked.connect(self.slot_publish)
        app.focusChanged.connect(self.focusChanged)
        self.text_open_button.clicked.connect(self.slot_open_dialog)
        self.live_save_button.clicked.connect(self.slot_save_live)
        self.preview_save_button.clicked.connect(self.slot_save_preview)


        self.text_db = list()
        #self.slot_load()
        self.next_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Space))
        self.next_button.clicked.connect(self.slot_next_item)

        self.previous_button.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Backspace))
        self.previous_button.clicked.connect(self.slot_previous_item)
        public_rect = self.live_text.geometry()
        global_rect = QtCore.QRect(self.mapToGlobal(public_rect.topLeft()), self.mapToGlobal(public_rect.bottomRight()))
        self.statusBar().showMessage("geometry to cast: %d, %d, %d, %d" % (global_rect.x(), global_rect.y(), global_rect.width(), global_rect.height()))

    def focusChanged(self, old, new):
        print "focusChanged", old, new
        if new == self.preview_text:
            try:
                self.removeToolBar(self.live_toolbar)
            except Exception, e:
                print e
            try:
                self.removeToolBar(self.preview_toolbar)
            except Exception, e:
                print e
            try:
                self.addToolBar(QtCore.Qt.BottomToolBarArea, self.preview_toolbar)
                self.preview_toolbar.show()
            except Exception, e:
                print e
        elif new == self.live_text:
            try:
                self.removeToolBar(self.live_toolbar)
            except Exception, e:
                print e
            try:
                self.removeToolBar(self.preview_toolbar)
            except Exception, e:
                print e
            try:
                self.addToolBar(QtCore.Qt.BottomToolBarArea, self.live_toolbar)
                self.live_toolbar.show()
            except Exception, e:
                print e


    def slot_next_item(self):
        print "slot_next_item"
        #print "current_title", self.current_title, self.current_text
        self.current = (self.current + 1) % len(self.text_db)
        self.preview_text.setTextOrHtml(self.text_db[self.current][1])
        print "current", self.current

    def slot_previous_item(self):
        print "slot_previous_item"
        #print "current_title", self.current_title, self.current_text
        self.current = (self.current - 1) % len(self.text_db)
        self.preview_text.setTextOrHtml(self.text_db[self.current][1])
        
        print "current", self.current

    def slot_toggleToolbox(self, index):
        print "slot_toggleToolbox"
        #print "current_title", self.current_title, self.current_text
        if index == 0:
            self.toolBar.setEnabled(True)
        else:
            self.toolBar.setEnabled(False)

    def slot_publish(self):
        print "slot_publish"
        public_rect = self.live_text.geometry()
        global_rect = QtCore.QRect(self.mapToGlobal(public_rect.topLeft()), self.mapToGlobal(public_rect.bottomRight()))
        self.statusBar().showMessage("geometry to cast: %d, %d, %d, %d" % (global_rect.x(), global_rect.y(), global_rect.width(), global_rect.height()))

        self.live_text.setTextOrHtml(self.preview_text.textOrHtml())
        self.is_published = True

    def slot_toggle_publish(self, state=None):
        #QPropertyAnimation animation(self.public_text.palette(), "geometry");
        #animation.setDuration(10000);
        #animation.setStartValue(QRect(0, 0, 100, 30));
        #animation.setEndValue(QRect(250, 250, 100, 30));
        #animation.start();
        print "slot_toggle_publish", state
        #print "current_title", self.current_title, self.current_text

        if state:
            self.slot_publish()
        else:
            self.slot_clear()

    def slot_clear_live(self):
        self.live_text.clear()
        self.is_published = False

    def slot_clear_preview(self):
        self.preview_text.clear()


    def slot_removeItem(self):
        text = self.edit_item_selection.currentText()
        index = self.edit_item_selection.currentIndex()
        title = text.split(": ")[1]
        del self.items[title]
        self.edit_item_selection.removeItem(index)
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
        self.preview_text.setTextOrHtml(text)
        self.item_title.setText(title)
        self.item_position_input.setValue(position)

    def slot_showLoadItem(self, index):
        public_rect = self.show_public_text.geometry()
        global_rect = QtCore.QRect(self.mapToGlobal(public_rect.topLeft()), self.mapToGlobal(public_rect.bottomRight()))
        self.statusBar().showMessage("geometry to cast: %d, %d, %d, %d" % (global_rect.x(), global_rect.y(), global_rect.width(), global_rect.height()))
        item = self.item_list.item(index)
        if item is None:
            return
        title = item.text()
        text, index = self.items[title]
        if self.auto_publish_checkbox.isChecked():
            self.live_text.setTextOrHtml(self.preview_text.textOrHtml())

    def title_by_index(self, ix):
        for title, (text, index) in self.items.iteritems():
            if index == ix:
                return title
        return None

    def slot_changeItem(self, old_title):
        print "slot_changeItem"
        text, index = self.items.pop(old_title)
        new_text = self.preview_text.textOrHtml()
        new_title = self.item_title.text()
        self.items[new_title] = (new_text, index)
        self.show_public_text.setTextOrHtml(new_text)
        self.item_title.setText(new_title)
        self.edit_item_selection.setItemText(index, "%d: %s" % (index, new_title))

    def slot_save_live(self):
        print "slot save live text"
        text = self.live_text.toHtml()
        preview = self.live_text.toPlainText()[:10]
        print "represent", preview
        self.text_db.append((preview, text))
    
    def slot_save_preview(self):
        print "slot save live text"
        text = self.preview_text.toHtml()
        preview = self.preview_text.toPlainText()[:10]
        print "represent", preview
        self.text_db.append((preview, text))

    def slot_save(self):
        cPickle.dump(self.items, open("448_texter.db", "w"), cPickle.HIGHEST_PROTOCOL)
    
    def slot_open_dialog(self):
        self.dialog = TextSorterDialog(self)
        print "modal", self.dialog.isModal()
        self.dialog.open()

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

        self.edit_item_selection.setCurrentIndex(0)
        title, text, index = data[0]

        self.preview_text.setTextOrHtml(text)
        self.item_position_input.setValue(index)
        self.item_title.setText(title)


def main():
    window = MainWindow()
    app.exec_()


if ( __name__ == '__main__' ):
    main()
