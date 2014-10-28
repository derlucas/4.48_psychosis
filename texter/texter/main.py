#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of texter package
#
# texter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# texter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with texter.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2014 Stefan Kögl

from __future__ import absolute_import


import cPickle
import os.path
import re
import sys
import traceback

from PyQt4 import QtCore, QtGui

from PyQt4.QtCore import QBuffer, QByteArray, QIODevice
from PyQt4.QtGui import QPixmap

from PyKDE4.kdeui import (KDialog, KActionCollection, KRichTextWidget,
    KRichTextWidget, KMainWindow, KToolBar, KAction, KToolBarSpacerAction,
    KSelectAction, KToggleAction, KShortcut)

from PyQt4.QtNetwork import QTcpServer, QTcpSocket

from chaosc.argparser_groups import ArgParser
from chaosc.lib import resolve_host, logger

from psylib.mjpeg_streaming_server import *
from psylib.psyqt_base import PsyQtClientBase

from texter.texter_ui import Ui_MainWindow, _fromUtf8
from texter.edit_dialog_ui import Ui_EditDialog
from texter.text_model import TextModel

qtapp = QtGui.QApplication([])


# NOTE: if the QIcon.fromTheme method does not find any icons, you can use
# qtconfig and set a default theme or copy|symlink an existing theme dir to hicolor
# in your local icon directory:
# ln -s /your/icon/theme/directory $HOME/.icons/hicolor

def get_preview_text(text):
    return re.sub(" +", " ", text.replace("\n", " ")).strip()[:20]


class EditDialog(QtGui.QWidget, Ui_EditDialog):
    def __init__(self, parent=None):
        super(EditDialog, self).__init__(parent)

        self.setupUi(self)
        self.model = None
        self.fill_list()

        self.text_list.clicked.connect(self.slot_show_text)
        self.remove_button.clicked.connect(self.slot_remove_item)
        self.move_up_button.clicked.connect(self.slot_text_up)
        self.move_down_button.clicked.connect(self.slot_text_down)
        self.text_list.clicked.connect(self.slot_toggle_buttons)
        self.move_up_button.setEnabled(False)
        self.move_down_button.setEnabled(False)


    def slot_toggle_buttons(self, index):
        row = index.row()
        if row <= 0:
            self.move_up_button.setEnabled(False)
        else:
            self.move_up_button.setEnabled(True)

        if row >= len(self.model.text_db) - 1:
            self.move_down_button.setEnabled(False)
        else:
            self.move_down_button.setEnabled(True)

    def fill_list(self):
        self.model = self.parent().parent().model
        self.text_list.setModel(self.model)
        index = self.parent().parent().current_index
        model_index = self.model.index(index, 0)
        self.text_list.setCurrentIndex(model_index)


    def slot_text_up(self):
        row = self.text_list.currentIndex().row()
        if row <= 0:
            return False

        text_db = self.model.text_db
        text_db[row-1], text_db[row] = text_db[row], text_db[row-1]
        self.text_list.setCurrentIndex(self.model.index(row - 1, 0))
        self.text_list.clicked.emit(self.model.index(row - 1, 0))
        self.parent().parent().db_dirty = True
        return True

    def slot_text_down(self):
        text_db = self.model.text_db
        row = self.text_list.currentIndex().row()
        if row >= len(text_db) - 1:
            return False

        text_db[row], text_db[row+1] = text_db[row+1], text_db[row]
        index = self.model.index(row + 1, 0)
        self.text_list.setCurrentIndex(index)
        self.text_list.clicked.emit(index)
        self.parent().parent().db_dirty = True
        return True

    def slot_show_text(self, model_index):
        try:
            self.text_preview.setHtml(self.parent().parent().model.text_db[model_index.row()][1])
        except IndexError:
            pass

    def slot_remove_item(self):
        index = self.text_list.currentIndex().row()
        self.model.removeRows(index, 1)
        index = self.model.index(0, 0)
        self.text_list.setCurrentIndex(index)
        self.text_list.clicked.emit(index)
        self.parent().parent().db_dirty = True

class TextAnimation(QtCore.QObject):
    animation_started = QtCore.pyqtSignal()
    animation_finished = QtCore.pyqtSignal()
    animation_stopped = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(TextAnimation, self).__init__(parent)
        self.src_text_edit = None
        self.cursor_position = 0
        self.src_cursor = None
        self.dst_text_edit = None
        self.dst_cursor = None
        self.src_block = None
        self.fragment_iter = None
        self.text = None
        self.it = None
        self.timer = None
        self.dst_current_block = None
        self.fonts = dict()
        self.count = 0

    def start_animation(self, src_text_edit, dst_text_edit, cursor_position):
        if self.timer is not None:
            return False
        self.parent().slot_clear_live()
        self.src_document = QtGui.QTextDocument(self)
        self.src_document.setHtml(src_text_edit.document().toHtml())
        self.src_text_edit = src_text_edit
        self.dst_text_edit = dst_text_edit
        self.cursor_position = cursor_position

        self.dst_cursor = self.dst_text_edit.textCursor()
        self.dst_cursor.setPosition(self.cursor_position)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.slot_animate)
        self.parent().slot_clear_live()
        self.timer.start(55)
        return True

    def slot_animate(self):
        self.animation_started.emit()

        if self.it is None:
            src_root_frame = self.src_document.rootFrame()
            self.it = src_root_frame.begin()
            self.dst_text_edit.document().rootFrame().setFrameFormat(src_root_frame.frameFormat())

        if not self.it.atEnd():
            if self.src_block is None:
                self.src_block = self.it.currentBlock()
                self.fragment_iter = self.src_block.begin()

                src_block_format = self.src_block.blockFormat()
                src_char_format = self.src_block.charFormat()
                if self.dst_current_block is not None:
                    self.dst_cursor.insertBlock(src_block_format)
                    self.dst_current_block = self.dst_current_block.next()
                else:
                    self.dst_current_block = self.dst_cursor.block()
                    self.dst_cursor.setBlockFormat(src_block_format)
                    self.dst_cursor.setBlockCharFormat(src_char_format)
                    self.dst_cursor.setCharFormat(src_char_format)

                self.dst_cursor.mergeBlockCharFormat(src_char_format)
                self.dst_cursor.mergeCharFormat(src_char_format)
                self.dst_cursor.mergeBlockFormat(src_block_format)

            if not self.fragment_iter.atEnd():
                if self.text is None:
                    fragment = self.fragment_iter.fragment()
                    self.text = iter(unicode(fragment.text()))
                    self.fragment_char_format = fragment.charFormat()
                    self.dst_cursor.setCharFormat(self.fragment_char_format)

                try:
                    char = self.text.next()
                    self.dst_cursor.insertText(char)
                    self.dst_text_edit.ensureCursorVisible()
                except StopIteration:
                    self.fragment_iter += 1
                    self.text = None
            else:
                self.it += 1
                self.src_block = None
        else:
            self.timer.stop()
            self.timer.timeout.disconnect(self.slot_animate)
            self.timer.deleteLater()
            self.dst_current_block = None
            self.it = None
            self.text = None
            self.animation_finished.emit()
            self.timer = None

        self.count += 1


class MainWindow(KMainWindow, Ui_MainWindow, MjpegStreamingConsumerInterface):
    def __init__(self, args, parent=None):
        self.args = args
        #super(MainWindow, self).__init__()
        #PsyQtClientBase.__init__(self)
        KMainWindow.__init__(self, parent)
        self.is_streaming = False

        self.live_center_action = None
        self.preview_center_action = None
        self.live_size_action = None
        self.preview_font_action = None
        self.live_font_action = None
        self.preview_size_action = None
        self.default_size = 28
        self.default_align_text = "format_align_center"
        self.preview_actions = list()
        self.live_actions = list()
        self.current = 0
        self.model = TextModel(self)
        self.animation = TextAnimation(self)
        self.db_dirty = False
        self.is_animate = False
        self.fade_animation = None
        self.dialog = None
        self.current_object = None
        self.current_index = -1

        self.is_auto_publish = False

        self.setupUi(self)
        self.win_id = self.live_text.winId()

        self.fps = 12.5
        self.http_server = MjpegStreamingServer((args.http_host, args.http_port), self, self.fps)

        self.live_text.setLineWrapMode(QtGui.QTextEdit.LineWrapMode(QtGui.QTextEdit.FixedPixelWidth))
        self.live_text.setLineWrapColumnOrWidth(768)

        self.font = QtGui.QFont("monospace", self.default_size)
        self.font.setStyleHint(QtGui.QFont.TypeWriter)

        self.previous_action = None
        self.next_action = None
        self.publish_action = None
        self.auto_publish_action = None
        self.save_live_action = None
        self.save_preview_action = None
        self.save_action = None
        self.dialog_widget = None
        self.action_collection = None
        self.streaming_action = None
        self.text_combo = None
        self.clear_live_action = None
        self.clear_preview_action = None
        self.toolbar = None
        self.typer_animation_action = None
        self.text_editor_action = None

        self.preview_text.setFont(self.font)
        self.preview_text.setRichTextSupport(KRichTextWidget.RichTextSupport(0xffffffff))
        self.preview_editor_collection = KActionCollection(self)
        self.preview_text.createActions(self.preview_editor_collection)

        self.live_text.setRichTextSupport(KRichTextWidget.RichTextSupport(0xffffffff))
        self.live_text.setFont(self.font)
        self.live_editor_collection = KActionCollection(self)
        self.live_text.createActions(self.live_editor_collection)
        self.filter_editor_actions()
        self.create_toolbar()
        self.slot_load()

        qtapp.focusChanged.connect(self.focusChanged)
        self.start_streaming()

        self.show()
        timer = QtCore.QTimer()
        timer.start(2000)
        timer.timeout.connect(lambda: None)

    def pubdir(self):
        return os.path.dirname(os.path.abspath(__file__))


    def getPreviewCoords(self):
        public_rect = self.preview_text.geometry()
        global_rect = QtCore.QRect(self.mapToGlobal(public_rect.topLeft()), self.mapToGlobal(public_rect.bottomRight()))
        return global_rect.x(), global_rect.y()

    def render_image(self):
        public_rect = self.live_text_rect()
        #global_rect = QtCore.QRect(self.mapToGlobal(public_rect.topLeft()), self.mapToGlobal(public_rect.bottomRight()))
        pixmap = QPixmap.grabWindow(self.win_id, public_rect.x() + 1, public_rect.y() + 1, 768, 576)
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        pixmap.save(buf, "JPG", 75)
        return buf.data()


    def filter_editor_actions(self):
        disabled_action_names = [
            "action_to_plain_text",
            "format_painter",
            "direction_ltr",
            "direction_rtl",
            "format_font_family",
            "format_text_background_color",
            "format_list_style",
            "format_list_indent_more",
            "format_list_indent_less",
            "format_text_bold",
            "format_text_underline",
            "format_text_strikeout",
            "format_text_italic",
            "format_align_right",
            "manage_link",
            "format_text_subscript",
            "format_text_superscript",
            "insert_horizontal_rule"
        ]

        for action in self.live_editor_collection.actions():
            text = str(action.objectName())
            if text in disabled_action_names:
                action.setVisible(False)

            if text == self.default_align_text:
                self.live_center_action = action
            elif text == "format_font_size":
                self.live_size_action = action
            elif text == "format_font_family":
                self.live_font_action = action

        for action in self.preview_editor_collection.actions():
            text = str(action.objectName())
            if text in disabled_action_names:
                action.setVisible(False)

            if text == self.default_align_text:
                self.preview_center_action = action
            elif text == "format_font_size":
                self.preview_size_action = action
            elif text == "format_font_family":
                self.preview_font_action = action

        self.slot_set_preview_defaults()
        self.slot_set_live_defaults()

    def create_toolbar(self):

        self.toolbar = KToolBar(self, True, True)
        self.toolbar.setIconDimensions(16)
        self.toolbar.setAllowedAreas(QtCore.Qt.BottomToolBarArea)
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.toolbar)

        self.toolbar.show()
        self.action_collection = KActionCollection(self)
        self.action_collection.addAssociatedWidget(self.toolbar)

        self.clear_live_action = self.action_collection.addAction("clear_live_action")
        icon = QtGui.QIcon(":texter/images/edit-clear.png")
        self.clear_live_action.setIcon(icon)
        self.clear_live_action.setIconText("clear live")
        self.clear_live_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_Q)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.save_live_action = self.action_collection.addAction("save_live_action")
        icon = QtGui.QIcon(":texter/images/document-new.png")
        self.save_live_action.setIcon(icon)
        self.save_live_action.setIconText("save live")
        self.save_live_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_W)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.clear_preview_action = self.action_collection.addAction("clear_preview_action")
        icon = QtGui.QIcon(":texter/images/edit-clear.png")
        self.clear_preview_action.setIcon(icon)
        self.clear_preview_action.setIconText("clear preview")
        self.clear_preview_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_A)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.save_preview_action = self.action_collection.addAction("save_preview_action")
        icon = QtGui.QIcon(":texter/images/document-new.png")
        self.save_preview_action.setIcon(icon)
        self.save_preview_action.setIconText("save preview")
        self.save_preview_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_S)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.publish_action = self.action_collection.addAction("publish_action")
        icon = QtGui.QIcon(":texter/images/edit-copy.png")
        self.publish_action.setIcon(icon)
        self.publish_action.setIconText("publish")
        self.publish_action.setShortcutConfigurable(True)
        self.publish_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_Return)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.toolbar.insertSeparator(self.publish_action)

        self.auto_publish_action = KToggleAction(self.action_collection)
        self.action_collection.addAction("auto publish", self.auto_publish_action)
        icon = QtGui.QIcon(":texter/images/view-refresh.png")
        self.auto_publish_action.setIcon(icon)
        self.auto_publish_action.setObjectName("auto_publish_action")
        self.auto_publish_action.setIconText("auto publish")
        self.auto_publish_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_P)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.typer_animation_action = KToggleAction(self.action_collection)
        icon = QtGui.QIcon(":texter/images/media-playback-stop.png")
        self.typer_animation_action.setIcon(icon)
        self.typer_animation_action.setIconText("animate")
        self.typer_animation_action.setObjectName("typer_animation_action")
        self.typer_animation_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_M)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))
        self.action_collection.addAction("typer_animation_action", self.typer_animation_action)

        self.text_editor_action = self.action_collection.addAction("text_editor_action")
        icon = QtGui.QIcon(":texter/images/document-open-data.png")
        self.text_editor_action.setIcon(icon)
        self.text_editor_action.setIconText("edit")
        self.text_editor_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_O)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.toolbar.insertSeparator(self.text_editor_action)

        self.save_action = self.action_collection.addAction("save_action")
        icon = QtGui.QIcon(":texter/images/document-save.png")
        self.save_action.setIcon(icon)
        self.save_action.setIconText("save")
        self.save_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_S)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.streaming_action = KToggleAction(self.action_collection)
        icon = QtGui.QIcon(":texter/images/media-record.png")
        self.streaming_action.setIcon(icon)
        self.streaming_action.setIconText("stream")
        self.streaming_action.setObjectName("stream")
        self.streaming_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_1)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))
        self.action_collection.addAction("stream", self.streaming_action)

        spacer = KToolBarSpacerAction(self.action_collection)
        self.action_collection.addAction("1_spacer", spacer)

        self.previous_action = self.action_collection.addAction("previous_action")
        icon = QtGui.QIcon(":texter/images/go-previous-view-page.png")
        self.previous_action.setIcon(icon)
        self.previous_action.setIconText("previous")
        self.previous_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_Left)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.text_combo = KSelectAction(self.action_collection)
        self.text_combo.setEditable(False)
        icon = QtGui.QIcon(":texter/images/document-open-recent.png")
        self.text_combo.setIcon(icon)
        self.text_combo.setIconText("saved texts")
        self.text_combo.setObjectName("text_combo")
        self.action_collection.addAction("saved texts", self.text_combo)

        self.next_action = self.action_collection.addAction("next_action")
        icon = QtGui.QIcon(":texter/images/go-next-view-page.png")
        self.next_action.setIcon(icon)
        self.next_action.setIconText("next")
        self.next_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_Right)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.toolbar.addSeparator()

        self.save_action.triggered.connect(self.slot_save)

        self.publish_action.triggered.connect(self.slot_publish)
        self.clear_live_action.triggered.connect(self.slot_clear_live)
        self.clear_preview_action.triggered.connect(self.slot_clear_preview)
        self.text_combo.triggered[int].connect(self.slot_load_preview_text)
        self.text_editor_action.triggered.connect(self.slot_open_dialog)
        self.save_live_action.triggered.connect(self.slot_save_live_text)
        self.save_preview_action.triggered.connect(self.slot_save_preview_text)
        self.streaming_action.triggered.connect(self.slot_toggle_streaming)
        self.auto_publish_action.toggled.connect(self.slot_auto_publish)
        self.typer_animation_action.toggled.connect(self.slot_toggle_animation)
        self.preview_size_action.triggered[QtGui.QAction].connect(self.slot_preview_font_size)
        self.live_size_action.triggered[QtGui.QAction].connect(self.slot_live_font_size)

        self.next_action.triggered.connect(self.slot_next_item)
        self.previous_action.triggered.connect(self.slot_previous_item)
        self.streaming_action.setChecked(True)

    def closeEvent(self, event):
        logger.info("closeEvent")
        if self.db_dirty:
            self.dialog = KDialog(self)
            self.dialog.setCaption("4.48 texter - text db not saved")
            label = QtGui.QLabel("The Text database is not saved. Do you want to save before exit?", self.dialog)
            self.dialog.setMainWidget(label)
            self.dialog.setButtons(KDialog.ButtonCodes(KDialog.Ok | KDialog.Cancel))
            self.dialog.okClicked.connect(self.slot_save)
            self.dialog.exec_()
        event.accept()

    def live_text_rect(self):
        return self.live_text.geometry()

    def stop_streaming(self):
        self.is_streaming = False
        self.http_server.stop()

    def start_streaming(self):
        self.http_server.listen(port=self.args.http_port)
        self.is_streaming = True

    def fill_combo_box(self):
        if self.dialog is not None:
            self.dialog.deleteLater()
            self.dialog = None

        self.text_combo.clear()
        current_row = -1
        for index, list_obj in enumerate(self.model.text_db):
            preview, text = list_obj
            self.text_combo.addAction(preview)
            if list_obj == self.current_object:
                current_row = index

        if current_row == -1:
            current_row = self.current_index
            self.slot_load_preview_text(current_row)
        self.text_combo.setCurrentItem(current_row)

    def focusChanged(self, old, new):
        if new == self.preview_text:
            self.live_editor_collection.clearAssociatedWidgets()
            self.preview_editor_collection.addAssociatedWidget(self.toolbar)
        elif new == self.live_text:
            self.preview_editor_collection.clearAssociatedWidgets()
            self.live_editor_collection.addAssociatedWidget(self.toolbar)

    def slot_auto_publish(self, state):
        self.is_auto_publish = bool(state)

    def slot_toggle_animation(self, state):
        self.is_animate = bool(state)

    def slot_toggle_streaming(self):
        if self.is_streaming:
            self.stop_streaming()
        else:
            self.start_streaming()

    def slot_next_item(self):
        try:
            self.current = (self.text_combo.currentItem() + 1) % len(self.model.text_db)
            self.text_combo.setCurrentItem(self.current)
            self.slot_load_preview_text(self.current)
        except ZeroDivisionError:
            pass

    def slot_previous_item(self):
        try:
            self.current = (self.text_combo.currentItem() - 1) % len(self.model.text_db)
            self.text_combo.setCurrentItem(self.current)
            self.slot_load_preview_text(self.current)
        except ZeroDivisionError:
            pass

    def slot_publish(self):
        if self.is_animate:
            self.animation.start_animation(self.preview_text, self.live_text, 0)
        else:
            self.live_text.setTextOrHtml(self.preview_text.textOrHtml())

    def slot_live_font_size(self, action):
        self.default_size = self.live_size_action.fontSize()
        self.slot_set_preview_defaults()
        self.slot_set_live_defaults()

    def slot_preview_font_size(self, action):
        self.default_size = self.preview_size_action.fontSize()
        self.slot_set_live_defaults()
        self.slot_set_preview_defaults()

    def slot_toggle_publish(self, state=None):

        if state:
            self.slot_publish()
        else:
            self.slot_clear_live()

    def slot_set_preview_defaults(self):
        self.preview_center_action.setChecked(True)
        self.preview_text.alignCenter()
        self.font.setPointSize(self.default_size)
        self.preview_text.setFontSize(self.default_size)
        self.preview_text.setFont(self.font)
        self.preview_size_action.setFontSize(self.default_size)
        self.preview_text.document().setDefaultFont(self.font)

    def slot_set_live_defaults(self):
        self.live_center_action.setChecked(True)
        self.live_text.alignCenter()
        self.live_text.setFontSize(self.default_size)
        self.live_size_action.setFontSize(self.default_size)
        self.live_text.document().setDefaultFont(self.font)

    def slot_clear_live(self):
        self.live_text.clear()
        self.slot_set_live_defaults()

    def slot_clear_preview(self):
        self.preview_text.clear()
        self.slot_set_preview_defaults()

    def slot_fade(self):
        if self.fade_animation.timer is None:
            self.fade_animation.start_animation()


    def slot_load_preview_text(self, index):
        try:
            preview, text = self.model.text_db[index]
        except IndexError:
            return
        self.preview_text.setTextOrHtml(text)
        if self.is_auto_publish:
            self.slot_publish()

    def slot_save_live_text(self):
        text = self.live_text.toHtml()
        preview = get_preview_text(unicode(self.live_text.toPlainText()))
        if not preview:
            return
        old_item = self.model.text_by_preview(preview)
        if old_item is not None:
            suffix = 1
            while 1:
                tmp_preview = "%s_%d" % (preview, suffix)
                tmp = self.model.text_by_preview(tmp_preview)
                if tmp is None:
                    preview = tmp_preview
                    break
                else:
                    suffix += 1

        self.model.text_db.append([preview, text])
        self.model.modelReset.emit()
        action = self.text_combo.addAction(preview)
        self.text_combo.setCurrentAction(action)
        self.db_dirty = True

    def slot_save_preview_text(self):
        text = self.preview_text.toHtml()
        preview = get_preview_text(unicode(self.preview_text.toPlainText()))

        if not preview:
            return
        old_item = self.model.text_by_preview(preview)
        if old_item is not None:
            ix, old_preview, old_text = old_item
            self.model.text_db[ix][1] = text
        else:
            self.model.text_db.append([preview, text])
            action = self.text_combo.addAction(preview)
            self.model.modelReset.emit()
            self.text_combo.setCurrentAction(action)
        self.db_dirty = True

    def slot_save(self):
        path = os.path.expanduser("~/.texter")
        if not os.path.isdir(path):
            os.mkdir(path)
        try:
            f = open(os.path.join(path, "texter.db"), "w")
        except IOError:
            return
        else:
            cPickle.dump(self.model.text_db, f, cPickle.HIGHEST_PROTOCOL)
        self.db_dirty = False

    def slot_open_dialog(self):
        self.current_index = self.text_combo.currentItem()
        self.current_object = self.model.text_db[self.current_index]
        if self.dialog is not None:
            self.dialog.deleteLater()
            self.dialog = None

        self.dialog = KDialog(self)
        self.dialog.setButtons(KDialog.Close)
        self.dialog_widget = EditDialog(self.dialog)
        self.dialog.setMainWidget(self.dialog_widget)
        pos_x, pos_y = self.getPreviewCoords()
        self.dialog.move(pos_x, self.pos().y())
        self.dialog.exec_()
        self.fill_combo_box()

    def slot_load(self):
        path = os.path.expanduser("~/.texter")
        if not os.path.isdir(path):
            os.mkdir(path)
        try:
            db_file = open(os.path.join(path, "texter.db"))
        except IOError:
            return

        try:
            self.model.text_db = [list(i) for i in cPickle.load(db_file)]
        except ValueError, error:
            logger.exception(error)

        self.fill_combo_box()
        self.text_combo.setCurrentItem(0)
        self.slot_load_preview_text(0)

    def sigint_handler(self, ex_cls, ex, tb):
        """Handler for the SIGINT signal."""
        if ex_cls == KeyboardInterrupt:
            logger.info("found KeyboardInterrupt")
            QtGui.QApplication.exit()
        else:
            logger.critical(''.join(traceback.format_tb(tb)))
            logger.critical('{0}: {1}'.format(ex_cls, ex))


def main():
    arg_parser = ArgParser("texter")
    arg_parser.add_global_group()
    client_group = arg_parser.add_client_group()
    arg_parser.add_argument(client_group, '-x', "--http_host", default="::",
        help='my host, defaults to "::"')
    arg_parser.add_argument(client_group, '-X', "--http_port", default=9001,
        type=int, help='my port, defaults to 9001')
    arg_parser.add_chaosc_group()
    arg_parser.add_subscriber_group()
    args = arg_parser.finalize()

    args.http_host, args.http_port = resolve_host(args.http_host, args.http_port, args.address_family)
    args.chaosc_host, args.chaosc_port = resolve_host(args.chaosc_host, args.chaosc_port, args.address_family)

    window = MainWindow(args, None)
    sys.excepthook = window.sigint_handler
    qtapp.exec_()


if __name__ == '__main__':
    main()
