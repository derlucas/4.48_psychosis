#!/usr/bin/python
# -*- coding: utf-8 -*-

import cPickle
import os.path
import re
import subprocess
import sys

from operator import itemgetter

from PyQt4 import QtCore, QtGui

from PyKDE4.kdecore import ki18n, KCmdLineArgs, KAboutData
from PyKDE4.kdeui import KActionCollection, KRichTextWidget, KComboBox, KPushButton, KRichTextWidget, KMainWindow, KToolBar, KApplication, KAction, KToolBarSpacerAction, KSelectAction, KToggleAction, KShortcut

from texter_ui import Ui_MainWindow, _fromUtf8
from text_sorter_ui import Ui_text_sorter_dialog

appName     = "texter"
catalog     = "448texter"
programName = ki18n("4.48 Psychose Texter")
version     = "0.1"

aboutData = KAboutData(appName, catalog, programName, version)

KCmdLineArgs.init (sys.argv, aboutData)

app = KApplication()

for path in QtGui.QIcon.themeSearchPaths():
    print "%s/%s" % (path, QtGui.QIcon.themeName())


# NOTE: if the QIcon.fromTheme method does not find any icons, you can set a theme
# in your local icon directory:
# ln -s /your/icon/theme/directory $HOME/.icons/hicolor

class TextSorterDialog(QtGui.QDialog, Ui_text_sorter_dialog):
    def __init__(self, parent = None):
        super(TextSorterDialog, self).__init__(parent)

        # setup the ui
        self.setupUi(self)
        self.setModal(False)
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
        self.parent().text_combo.clear()
        parent = self.parent()
        for preview in self.text_list.items():
            pre, text = parent.text_by_preview(preview)
            print "pre, text", pre, preview
            data.append((preview, text))
            parent.text_combo.addAction(preview)
            parent.text_combo.setCurrentItem(0)
        parent.text_db = data
        parent.slot_load_preview_text(0)
        parent.slot_set_live_defaults()
        parent.slot_set_preview_defaults()


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
        self.default_font = None
        self.default_align_text = "format_align_center"
        self.preview_actions = list()
        self.live_actions = list()
        self.is_published = False
        self.current = 0
        self.text_db = list()
        self.is_auto_publish = False

        self.setupUi(self)

        self.font = QtGui.QFont("monospace", 22)
        self.font.setStyleHint(QtGui.QFont.TypeWriter)

        self.toolbar = KToolBar(self, True, True)
        self.toolbar.setAllowedAreas(QtCore.Qt.BottomToolBarArea)
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.toolbar)
        self.createLiveActions()
        self.createPreviewActions()


        self.preview_text.document().setDefaultFont(self.font)
        self.preview_text.setRichTextSupport(KRichTextWidget.RichTextSupport(0xffffffff))
        self.preview_editor_collection = KActionCollection(self)
        self.preview_text.createActions(self.preview_editor_collection)

        self.live_text.setRichTextSupport(KRichTextWidget.RichTextSupport(0xffffffff))
        self.live_text.document().setDefaultFont(self.font)
        self.live_editor_collection = KActionCollection(self)
        self.live_text.createActions(self.live_editor_collection)
        self.filter_editor_actions()
        self.toolbar.insertSeparator(self.publish_action)
        self.toolbar.addSeparator()

        self.show()


        self.save_action.triggered.connect(self.slot_save)
        self.publish_action.triggered.connect(self.slot_publish)
        self.clear_live_action.triggered.connect(self.slot_clear_live)
        self.clear_preview_action.triggered.connect(self.slot_clear_preview)
        #self.remove_item_button.triggered.connect(self.slot_removeItem)
        self.text_combo.triggered[int].connect(self.slot_load_preview_text)

        app.focusChanged.connect(self.focusChanged)
        self.text_editor_action.triggered.connect(self.slot_open_dialog)
        self.save_live_action.triggered.connect(self.slot_save_live_text)
        self.save_preview_action.triggered.connect(self.slot_save_preview_text)
        self.streaming_action.triggered.connect(self.slot_toggle_streaming)
        self.auto_publish_action.toggled.connect(self.slot_auto_publish)

        self.slot_load()
        self.next_action.triggered.connect(self.slot_next_item)
        self.previous_action.triggered.connect(self.slot_previous_item)

        app.aboutToQuit.connect(self.kill_streaming)
        self.getLiveCoords()


    def getLiveCoords(self):
        public_rect = self.live_text.geometry()
        global_rect = QtCore.QRect(self.mapToGlobal(public_rect.topLeft()), self.mapToGlobal(public_rect.bottomRight()))
        x = global_rect.x()
        y = global_rect.y()
        self.statusBar().showMessage("live text editor dimensions: x=%r, y=%r, width=%r, height=%r" % (x, y, global_rect.width(), global_rect.height()))


    def filter_editor_actions(self):

        disabled_action_names = [
            "action_to_plain_text",
            "format_painter",
            "direction_ltr",
            "direction_rtl",
            "format_font_family",
            "format_font_size",
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


        print "live_center_action", self.live_center_action
        print "live_size_action", self.live_size_action
        print "preview_center_action", self.preview_center_action
        print "preview_size_action", self.preview_size_action
        #print "widgets", self.preview_font_action.associatedGraphicsWidgets()
        self.slot_set_preview_defaults()
        self.slot_set_live_defaults()


    def createLiveActions(self):
        self.toolbar.show()
        self.live_text_collection = KActionCollection(self)
        self.live_text_collection.addAssociatedWidget(self.toolbar)

        self.clear_live_action = self.live_text_collection.addAction("clear_live_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("edit-clear"))
        self.clear_live_action.setIcon(icon)
        self.clear_live_action.setIconText("clear live")
        self.clear_live_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_Q)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))


        self.save_live_action = self.live_text_collection.addAction("save_live_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("document-new"))
        self.save_live_action.setIcon(icon)
        self.save_live_action.setIconText("save live")
        self.save_live_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_W)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))



    def createPreviewActions(self):
        self.toolbar.show()
        self.preview_text_collection = KActionCollection(self)
        self.preview_text_collection.addAssociatedWidget(self.toolbar)

        self.clear_preview_action = self.preview_text_collection.addAction("clear_preview_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("edit-clear"))
        self.clear_preview_action.setIcon(icon)
        self.clear_preview_action.setIconText("clear preview")
        #self.clear_preview_action.setObjectName("clear_preview")
        self.clear_preview_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_A)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))


        self.save_preview_action = self.preview_text_collection.addAction("save_preview_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("document-new"))
        self.save_preview_action.setIcon(icon)
        self.save_preview_action.setIconText("save preview")
        self.save_preview_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_S)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))


        self.publish_action = self.preview_text_collection.addAction("publish_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("media-playback-start"))
        self.publish_action.setIcon(icon)
        self.publish_action.setIconText("publish")
        self.publish_action.setShortcutConfigurable(True)
        self.publish_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_Return)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))


        self.previous_action = self.preview_text_collection.addAction("previous_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("media-skip-backward"))
        self.previous_action.setIcon(icon)
        self.previous_action.setIconText("previous")
        self.previous_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_Left)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.text_combo = KSelectAction(self.preview_text_collection)
        self.text_combo.setEditable(False)
        self.text_combo.setComboWidth(100)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("document-open-recent"))
        self.text_combo.setIcon(icon)
        self.text_combo.setIconText("saved texts")
        self.text_combo.setObjectName("text_combo")
        self.preview_text_collection.addAction("saved texts", self.text_combo)

        self.next_action = self.preview_text_collection.addAction("next_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("media-skip-forward"))
        self.next_action.setIcon(icon)
        self.next_action.setIconText("next")
        self.next_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.ALT + QtCore.Qt.Key_Right)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.text_editor_action = KToggleAction(self.preview_text_collection)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("document-open"))
        self.text_editor_action.setIcon(icon)
        self.text_editor_action.setIconText("sort")
        self.preview_text_collection.addAction("text editor", self.text_editor_action)
        self.text_editor_action.setObjectName("text_editor_action")
        self.text_editor_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_O)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.auto_publish_action = KToggleAction(self.preview_text_collection)
        self.preview_text_collection.addAction("auto publish", self.auto_publish_action)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("view-refresh"))
        self.auto_publish_action.setIcon(icon)
        self.auto_publish_action.setObjectName("auto_publish_action")
        self.auto_publish_action.setIconText("auto publish")

        self.save_action = self.preview_text_collection.addAction("save_action")
        icon = QtGui.QIcon.fromTheme(_fromUtf8("document-save"))
        self.save_action.setIcon(icon)
        self.save_action.setIconText("save")
        self.save_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_S)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))

        self.streaming_action = KToggleAction(self.live_text_collection)
        icon = QtGui.QIcon.fromTheme(_fromUtf8("media-record"))
        self.streaming_action.setIcon(icon)
        self.streaming_action.setIconText("stream")
        self.streaming_action.setObjectName("stream")
        self.streaming_action.setShortcut(KShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_1)), KAction.ShortcutTypes(KAction.ActiveShortcut | KAction.DefaultShortcut))
        self.live_text_collection.addAction("stream", self.streaming_action)


    def slot_auto_publish(self, state):
        print "auto_publish", state
        self.is_auto_publish = bool(state)


    def slot_toggle_streaming(self):
        if self.ffserver is None:
            self.start_streaming()
        else:
            self.kill_streaming()


    def kill_streaming(self):
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
        self.ffserver = subprocess.Popen("/usr/bin/ffserver -f /etc/ffserver.conf", shell=True, close_fds=True)
        self.ffmpeg = subprocess.Popen("/usr/bin/ffmpeg -f x11grab -s 768x576 -r 25 -i :0.0+%d,%d -vcodec mjpeg -pix_fmt yuvj422p -r 25 -aspect 4:3 http://localhost:8090/webcam.ffm" % (global_rect.x(), global_rect.y()), shell=True, close_fds=True)
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
        return re.sub(" +", " ", text.replace("\n", " "))[:20]


    def text_by_preview(self, preview):
        for title, text in self.text_db:
            if title == preview:
                return title, text
        return None


    def title_by_index(self, ix):
        for title, (text, index) in self.items.iteritems():
            if index == ix:
                return title
        return None


    def slot_next_item(self):
        self.current = (self.text_combo.currentItem() + 1) % len(self.text_db)
        self.text_combo.setCurrentItem(self.current)
        self.slot_load_preview_text(self.current)


    def slot_previous_item(self):
        #print "current_title", self.current_title, self.current_text
        self.current = (self.text_combo.currentItem() - 1) % len(self.text_db)
        self.text_combo.setCurrentItem(self.current)
        self.slot_load_preview_text(self.current)


    def slot_toggleToolbox(self, index):
        #print "current_title", self.current_title, self.current_text
        if index == 0:
            self.toolBar.setEnabled(True)
        else:
            self.toolBar.setEnabled(False)


    def slot_publish(self):
        self.live_text.setTextOrHtml(self.preview_text.textOrHtml())
        self.is_published = True


    def slot_toggle_publish(self, state=None):

        if state:
            self.slot_publish()
        else:
            self.slot_clear_live()


    def slot_set_preview_defaults(self):
        self.preview_center_action.setChecked(True)
        self.preview_text.alignCenter()
        self.preview_size_action.setFontSize(self.default_size)
        #self.preview_size_action.fontSizeChanged.emit(self.default_size)
        self.preview_text.setFontSize(self.default_size)


    def slot_set_live_defaults(self):
        self.live_center_action.setChecked(True)
        self.live_text.alignCenter()
        self.live_size_action.setFontSize(self.default_size)
        self.live_text.setFontSize(self.default_size)


    def slot_clear_live(self):
        self.default_size = self.live_size_action.fontSize()
        self.is_published = False
        cursor = self.live_text.textCursor()
        self.custom_clear(cursor)
        self.slot_set_live_defaults()


    def slot_clear_preview(self):
        #self.preview_text.document().clear()
        self.default_size = self.preview_size_action.fontSize()
        cursor = self.preview_text.textCursor()
        self.custom_clear(cursor)
        self.slot_set_preview_defaults()


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

    def slot_load_preview_text(self, index):
        preview, text = self.text_db[index]
        self.preview_text.setTextOrHtml(text)
        if self.is_auto_publish:
            self.live_text.setTextOrHtml(text)


    def slot_save_live_text(self):
        text = self.live_text.toHtml()
        preview = self.get_preview_text(unicode(self.live_text.toPlainText()))
        if not preview:
            return
        old_item = self.text_by_preview(preview)
        if old_item is not None:
            suffix = 1
            while 1:
                tmp_preview = "%s_%d" % (preview, suffix)
                tmp = self.text_by_preview(tmp_preview)
                if tmp is None:
                    preview = tmp_preview
                    break
                else:
                    suffix += 1

        self.text_db.append((preview, text))
        action = self.text_combo.addAction(preview)
        self.text_combo.setCurrentAction(action)

    def slot_save_preview_text(self):
        text = self.preview_text.toHtml()
        preview = self.get_preview_text(unicode(self.preview_text.toPlainText()))

        if not preview:
            return
        old_item = self.text_by_preview(preview)
        if old_item is not None:
            suffix = 1
            while 1:
                tmp_preview = "%s_%d" % (preview, suffix)
                tmp = self.text_by_preview(tmp_preview)
                if tmp is None:
                    preview = tmp_preview
                    break
                else:
                    suffix += 1

        self.text_db.append((preview, text))
        action = self.text_combo.addAction(preview)
        self.text_combo.setCurrentAction(action)

    def slot_save(self):
        cPickle.dump(self.text_db, open("448_texter.db", "w"), cPickle.HIGHEST_PROTOCOL)

    def slot_open_dialog(self):
        self.dialog = TextSorterDialog(self)
        self.dialog.open()

    def slot_load(self):
        try:
            self.text_db = cPickle.load(open("448_texter.db"))
        except Exception, e:
            print e

        data = list()
        for title, text in self.text_db:
            data.append((title, text))
            self.text_combo.addAction(title)

        self.text_combo.setCurrentItem(0)
        self.slot_load_preview_text(0)


def main():
    window = MainWindow()
    app.exec_()


if ( __name__ == '__main__' ):
    main()
