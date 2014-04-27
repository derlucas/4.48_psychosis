#!/usr/bin/python
# -*- coding: utf-8 -*-

import cPickle
import os.path
import re
import subprocess
import sys
from math import pow

from operator import itemgetter

from PyQt4 import QtCore, QtGui


from PyKDE4.kdecore import ki18n, KCmdLineArgs, KAboutData
from PyKDE4.kdeui import KDialog, KActionCollection, KRichTextWidget, KComboBox, KPushButton, KRichTextWidget, KMainWindow, KToolBar, KApplication, KAction, KToolBarSpacerAction, KSelectAction, KToggleAction, KShortcut

from texter_ui import Ui_MainWindow, _fromUtf8
from text_sorter_ui import Ui_TextSorterDialog
from text_model import TextModel

appName     = "texter"
catalog     = "448texter"
programName = ki18n("4.48 Psychose Texter")
version     = "0.1"

aboutData = KAboutData(appName, catalog, programName, version)

KCmdLineArgs.init (sys.argv, aboutData)

app = KApplication()

for path in QtGui.QIcon.themeSearchPaths():
    print "%s/%s" % (path, QtGui.QIcon.themeName())


# NOTE: if the QIcon.fromTheme method does not find any icons, you can use
# qtconfig and set a default theme or copy|symlink an existing theme dir to hicolor
# in your local icon directory:
# ln -s /your/icon/theme/directory $HOME/.icons/hicolor

class TextSorterDialog(QtGui.QWidget, Ui_TextSorterDialog):
    def __init__(self, parent = None):
        super(TextSorterDialog, self).__init__(parent)

        self.setupUi(self)
        self.fill_list()

        self.text_list.clicked.connect(self.slot_show_text)
        self.remove_button.clicked.connect(self.slot_removeItem)
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

    def slot_text_up(self):
        row = self.text_list.currentIndex().row()
        if row <= 0:
            return False

        text_db = self.model.text_db
        text_db[row-1], text_db[row] = text_db[row], text_db[row-1]
        self.text_list.setCurrentIndex(self.model.index(row - 1, 0))
        self.text_list.clicked.emit(self.model.index(row - 1, 0))
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
        return True

    def slot_show_text(self, model_index):
        try:
            self.text_preview.setTextOrHtml(self.parent().parent().model.text_db[model_index.row()][1])
        except IndexError:
            pass


    def slot_removeItem(self):
        index = self.text_list.currentIndex().row()
        self.model.removeRows(index, 1)
        index = self.model.index(0, 0)
        self.text_list.setCurrentIndex(index)
        self.text_list.clicked.emit(index)

class FadeAnimation(QtCore.QObject):
    animation_started = QtCore.pyqtSignal()
    animation_finished = QtCore.pyqtSignal()
    animation_stopped = QtCore.pyqtSignal()

    def __init__(self, live_text, fade_steps=6, parent=None):
        super(FadeAnimation, self).__init__(parent)
        self.live_text = live_text
        self.fade_steps = fade_steps
        self.current_alpha = 255
        self.timer = None
    
    
    def start_animation(self):
        print "start_animation"
        self.animation_started.emit()

        if self.current_alpha == 255:
            self.fade_delta = 255 / self.fade_steps
        else:
            self.fade_delta = -255 / self.fade_steps
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.slot_animate)
        self.timer.start(100)


    def slot_animate(self):
        print "slot_animate"
        print "current_alpha", self.current_alpha
        if self.fade_delta > 0:
            if self.current_alpha > 0:
                self.live_text.setStyleSheet("color:%d, %d, %d;" % (self.current_alpha, self.current_alpha,self.current_alpha))
                self.current_alpha -= self.fade_delta
            else:
                self.live_text.setStyleSheet("color:black;")
                self.current_alpha = 0
                self.timer.stop()
                self.timer.timeout.disconnect(self.slot_animate)
                self.timer.deleteLater()
                self.timer = None
                self.animation_finished.emit()
                print "animation_finished"
        else:
            if self.current_alpha < 255:
                self.live_text.setStyleSheet("color:%d,%d, %d;" % (self.current_alpha, self.current_alpha,self.current_alpha))
                self.current_alpha -= self.fade_delta
            else:
                self.live_text.setStyleSheet("color:white")
                self.current_alpha = 255
                self.timer.stop()
                self.timer.timeout.disconnect(self.slot_animate)
                self.timer.deleteLater()
                self.timer = None
                self.animation_finished.emit()
                print "animation_finished"

    

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
        parent = self.parent()

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


class MainWindow(KMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.is_streaming = False
        self.ffserver = None
        self.ffmpeg = None
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

        self.is_auto_publish = False

        self.setupUi(self)
        
        self.fade_animation = FadeAnimation(self.live_text, 6, self)

        self.font = QtGui.QFont("monospace", self.default_size)
        self.font.setStyleHint(QtGui.QFont.TypeWriter)


        self.create_toolbar()

        #self.preview_text.document().setDefaultFont(self.font)
        self.preview_text.setFont(self.font)
        self.preview_text.setRichTextSupport(KRichTextWidget.RichTextSupport(0xffffffff))
        self.preview_editor_collection = KActionCollection(self)
        self.preview_text.createActions(self.preview_editor_collection)

        self.live_text.setRichTextSupport(KRichTextWidget.RichTextSupport(0xffffffff))
        #self.live_text.document().setDefaultFont(self.font)
        self.live_text.setFont(self.font)
        self.live_editor_collection = KActionCollection(self)
        self.live_text.createActions(self.live_editor_collection)
        self.filter_editor_actions()
        self.slot_load()

        self.show()

        self.save_action.triggered.connect(self.slot_save)

        self.publish_action.triggered.connect(self.slot_publish)
        self.clear_live_action.triggered.connect(self.slot_clear_live)
        self.clear_preview_action.triggered.connect(self.slot_clear_preview)
        self.text_combo.triggered[int].connect(self.slot_load_preview_text)

        app.focusChanged.connect(self.focusChanged)
        self.text_editor_action.triggered.connect(self.slot_open_dialog)
        self.save_live_action.triggered.connect(self.slot_save_live_text)
        self.save_preview_action.triggered.connect(self.slot_save_preview_text)
        self.streaming_action.triggered.connect(self.slot_toggle_streaming)
        self.auto_publish_action.toggled.connect(self.slot_auto_publish)
        self.typer_animation_action.toggled.connect(self.slot_toggle_animation)
        self.preview_size_action.triggered[QtGui.QAction].connect(self.slot_preview_font_size)
        self.live_size_action.triggered[QtGui.QAction].connect(self.slot_live_font_size)

        self.fade_action.triggered.connect(self.slot_fade)
        self.next_action.triggered.connect(self.slot_next_item)
        self.previous_action.triggered.connect(self.slot_previous_item)

        self.getLiveCoords()
        print "desktop", app.desktop().availableGeometry()


    def getLiveCoords(self):
        public_rect = self.live_text.geometry()
        global_rect = QtCore.QRect(self.mapToGlobal(public_rect.topLeft()), self.mapToGlobal(public_rect.bottomRight()))
        x = global_rect.x()
        y = global_rect.y()
        self.statusBar().showMessage("live text editor dimensions: x=%r, y=%r, width=%r, height=%r" % (x, y, global_rect.width(), global_rect.height()))

    def getPreviewCoords(self):
        public_rect = self.preview_text.geometry()
        global_rect = QtCore.QRect(self.mapToGlobal(public_rect.topLeft()), self.mapToGlobal(public_rect.bottomRight()))
        return global_rect.x(), global_rect.y()


    def filter_editor_actions(self):

        disabled_action_names = [
            "action_to_plain_text",
            "format_painter",
            "direction_ltr",
            "direction_rtl",
            "format_font_family",
            #"format_font_size",
            "format_text_background_color",
            "format_list_indent_more",
            "format_list_indent_less",
            "format_text_bold",
            "format_text_underline",
            "format_text_strikeout",
            "format_text_italic",
            "format_align_right",
            "format_align_justify",
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
        self.toolbar.setAllowedAreas(QtCore.Qt.BottomToolBarArea)
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.toolbar)

        self.toolbar.show()
        self.action_collection = KActionCollection(self)
        self.action_collection.addAssociatedWidget(self.toolbar)

        self.clear_live_action = self.action_collection.addAction("clear_live_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("edit-clear"))
        self.clear_live_action.setIcon(icon)
        self.clear_live_action.setIconText("clear live")
        self.clear_live_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_Q)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.save_live_action = self.action_collection.addAction("save_live_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("document-new"))
        self.save_live_action.setIcon(icon)
        self.save_live_action.setIconText("save live")
        self.save_live_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_W)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.clear_preview_action = self.action_collection.addAction("clear_preview_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("edit-clear"))
        self.clear_preview_action.setIcon(icon)
        self.clear_preview_action.setIconText("clear preview")
        #self.clear_preview_action.setObjectName("clear_preview")
        self.clear_preview_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_A)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.save_preview_action = self.action_collection.addAction("save_preview_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("document-new"))
        self.save_preview_action.setIcon(icon)
        self.save_preview_action.setIconText("save preview")
        self.save_preview_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_S)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.publish_action = self.action_collection.addAction("publish_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("edit-copy"))
        self.publish_action.setIcon(icon)
        self.publish_action.setIconText("publish")
        self.publish_action.setShortcutConfigurable(True)
        self.publish_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_Return)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.toolbar.insertSeparator(self.publish_action)

        self.auto_publish_action = KToggleAction(self.action_collection)
        self.action_collection.addAction("auto publish", self.auto_publish_action)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("view-refresh"))
        self.auto_publish_action.setIcon(icon)
        self.auto_publish_action.setObjectName("auto_publish_action")
        self.auto_publish_action.setIconText("auto publish")
        self.auto_publish_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_P)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.typer_animation_action = KToggleAction(self.action_collection)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("media-playback-stop"))
        self.typer_animation_action.setIcon(icon)
        self.typer_animation_action.setIconText("animate")
        self.typer_animation_action.setObjectName("typer_animation_action")
        self.typer_animation_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_M)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))
        self.action_collection.addAction("typer_animation_action", self.typer_animation_action)

        self.text_editor_action = self.action_collection.addAction("text_editor_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("document-open-data"))
        self.text_editor_action.setIcon(icon)
        self.text_editor_action.setIconText("edit")
        self.text_editor_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_O)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.toolbar.insertSeparator(self.text_editor_action)

        self.save_action = self.action_collection.addAction("save_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("document-save"))
        self.save_action.setIcon(icon)
        self.save_action.setIconText("save")
        self.save_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_S)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.streaming_action = KToggleAction(self.action_collection)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("media-record"))
        self.streaming_action.setIcon(icon)
        self.streaming_action.setIconText("stream")
        self.streaming_action.setObjectName("stream")
        self.streaming_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_1)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))
        self.action_collection.addAction("stream", self.streaming_action)

        spacer = KToolBarSpacerAction(self.action_collection)
        self.action_collection.addAction("1_spacer", spacer)
        
        self.fade_action = self.action_collection.addAction("fade_action")
        #icon = QtGui.QIcon.fromTheme(_fromUtf8("go-previous-view-page"))
        #self.fade_action.setIcon(icon)
        self.fade_action.setIconText("fade")
        self.fade_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_F)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.previous_action = self.action_collection.addAction("previous_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("go-previous-view-page"))
        self.previous_action.setIcon(icon)
        self.previous_action.setIconText("previous")
        self.previous_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_Left)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.text_combo = KSelectAction(self.action_collection)
        self.text_combo.setEditable(False)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("document-open-recent"))
        self.text_combo.setIcon(icon)
        self.text_combo.setIconText("saved texts")
        self.text_combo.setObjectName("text_combo")
        self.action_collection.addAction("saved texts", self.text_combo)

        self.next_action = self.action_collection.addAction("next_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("go-next-view-page"))
        self.next_action.setIcon(icon)
        self.next_action.setIconText("next")
        self.next_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_Right)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.toolbar.addSeparator()


    def closeEvent(self, event):
        self.stop_streaming()
        if self.db_dirty:
            self.dialog = KDialog(self)
            self.dialog.setCaption("4.48 texter - text db not saved")
            label = QtGui.QLabel("The Text database is not saved. Do you want to save before exit?", self.dialog)
            self.dialog.setMainWidget(label)
            self.dialog.setButtons(KDialog.ButtonCodes(KDialog.Ok | KDialog.Cancel))
            self.dialog.okClicked.connect(self.slot_save)
            self.dialog.exec_()

    def stop_streaming(self):
        self.is_streaming = False
        if self.ffmpeg is not None:
            self.ffmpeg.kill()
            self.ffmpeg = None
        if self.ffserver is not None:
            self.ffserver.kill()
            self.ffserver = None

    def start_streaming(self):
        public_rect = self.live_text.geometry()
        global_rect = QtCore.QRect(self.mapToGlobal(public_rect.topLeft()), self.mapToGlobal(public_rect.bottomRight()))
        self.ffserver = subprocess.Popen("ffserver -f /etc/ffserver.conf", shell=True, close_fds=True)
        self.ffmpeg = subprocess.Popen("ffmpeg -f x11grab -s 768x576 -r 30 -i :0.0+%d,%d -vcodec mjpeg -pix_fmt yuvj444p -r 30 -aspect 4:3 http://localhost:8090/webcam.ffm" % (global_rect.x()+5, global_rect.y()+5), shell=True, close_fds=True)
        self.is_streaming = True

    def focusChanged(self, old, new):
        if new == self.preview_text:
            self.live_editor_collection.clearAssociatedWidgets()
            self.preview_editor_collection.addAssociatedWidget(self.toolbar)
        elif new == self.live_text:
            self.preview_editor_collection.clearAssociatedWidgets()
            self.live_editor_collection.addAssociatedWidget(self.toolbar)

    def custom_clear(self, cursor):
        cursor.beginEditBlock()
        cursor.movePosition(QtGui.QTextCursor.Start);
        cursor.movePosition(QtGui.QTextCursor.End, QtGui.QTextCursor.KeepAnchor);
        cursor.removeSelectedText()
        cursor.endEditBlock()


    def get_preview_text(self, text):
        return re.sub(" +", " ", text.replace("\n", " ")).strip()[:20]


    def slot_auto_publish(self, state):
        self.is_auto_publish = bool(state)

    def slot_toggle_animation(self, state):
        self.is_animate = bool(state)

    def slot_toggle_streaming(self):
        if self.ffserver is None:
            self.start_streaming()
        else:
            self.stop_streaming()


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


    def fill_combo_box(self):
        self.text_combo.clear()
        for preview, text in self.model.text_db:
            self.text_combo.addAction(preview)

        self.text_combo.setCurrentItem(0)
        self.slot_load_preview_text(0)


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
        preview = self.get_preview_text(unicode(self.live_text.toPlainText()))
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
        preview = self.get_preview_text(unicode(self.preview_text.toPlainText()))

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
        self.dialog = KDialog(self)
        self.dialog_widget = TextSorterDialog(self.dialog)
        self.dialog.setMainWidget(self.dialog_widget)
        pos_x, pos_y = self.getPreviewCoords()
        self.dialog.move(pos_x, 0)
        rect = app.desktop().availableGeometry()
        global_width = rect.width()
        global_height = rect.height()
        x = global_width - pos_x - 10
        #self.dialog.setFixedSize(x, global_height-40)
        self.dialog.okClicked.connect(self.fill_combo_box)
        self.dialog.exec_()
        self.dialog.deleteLater()
        self.dialog = None

    def slot_load(self):
        path = os.path.expanduser("~/.texter")
        if not os.path.isdir(path):
            os.mkdir(path)
        try:
            f = open(os.path.join(path, "texter.db"))
        except IOError:
            return

        try:
            self.model.text_db = [list(i) for  i in cPickle.load(f)]
        except Exception, e:
            print e

        self.fill_combo_box()
        self.text_combo.setCurrentItem(0)
        self.slot_load_preview_text(0)



def main():
    window = MainWindow()
    app.exec_()


if ( __name__ == '__main__' ):
    main()
