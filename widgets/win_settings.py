import os
import shutil
import subprocess

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import (QApplication, QFileDialog, QLabel, QSpacerItem,
                             QTextEdit, QWidget)

from base_widgets import Btn, CustomTextEdit, InputBase, LayoutHor, LayoutVer
from base_widgets.wins import WinChild
from cfg import APP_SUPPORT_DIR, DB_FILE, HASH_DIR, JsonData
from lng import Lng
from utils.scaner import Scaner
from utils.updater import Updater
from utils.utils import UThreadPool, Utils

from .actions import OpenWins


class BrowseColl(QWidget):
    def __init__(self):
        super().__init__()
        self.new_coll_path = None

        layout_h = LayoutHor()
        self.setLayout(layout_h)

        self.browse_btn = Btn(Lng.browse)
        self.browse_btn.mouseReleaseEvent = self.choose_folder
        layout_h.addWidget(self.browse_btn)

        layout_h.addSpacerItem(QSpacerItem(10, 0))

        self.coll_path_label = QLabel(self.cut_text(JsonData.coll_folder))
        self.coll_path_label.setWordWrap(True)
        self.coll_path_label.setFixedHeight(35)
        layout_h.addWidget(self.coll_path_label)

    def choose_folder(self, e):
        file_dialog = QFileDialog()
        file_dialog.setOption(QFileDialog.ShowDirsOnly, True)

        if self.new_coll_path:
            file_dialog.setDirectory(self.new_coll_path)

        elif not os.path.exists(JsonData.coll_folder):
            file_dialog.setDirectory(JsonData.down_folder)

        else:
            file_dialog.setDirectory(JsonData.coll_folder)

        selected_folder = file_dialog.getExistingDirectory()

        if selected_folder:
            self.new_coll_path = selected_folder
            self.coll_path_label.setText(self.cut_text(self.new_coll_path))

    def cut_text(self, text: str, max_ln: int = 70):
        if len(text) > max_ln:
            return text[:max_ln] + "..."
        else:
            return text


class CollFolderListInput(CustomTextEdit):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(130)
        self.setLineWrapMode(QTextEdit.NoWrap)
        h_bar = self.horizontalScrollBar()
        h_bar.setFixedHeight(0)

        text = "\n".join(JsonData.coll_folder_list)
        self.setText(text)

    def get_text(self):
        text = self.toPlainText()
        coll_folder_list = text.split("\n")


        coll_folder_list = [
            os.sep + i.strip().strip(os.sep)
            for i in coll_folder_list
            ]
        
        return coll_folder_list


class ChangeLang(QWidget):
    _pressed = pyqtSignal()

    def __init__(self):
        super().__init__()

        layout_h = LayoutHor()
        self.setLayout(layout_h)

        self.lang_btn = Btn(Lng.lang_name)
        self.lang_btn.mouseReleaseEvent = self.lng_cmd
        layout_h.addWidget(self.lang_btn)

        layout_h.addSpacerItem(QSpacerItem(10, 0))

        self.lang_label = QLabel(Lng.lang_label)
        layout_h.addWidget(self.lang_label)
          
    def lng_cmd(self, e):

        if JsonData.lng_ind == 0:
            JsonData.lng_ind = 1

        elif JsonData.lng_ind == 1:
            JsonData.lng_ind = 0

        self.lang_btn.setText(Lng.lang_name)
        setattr(self, "flag", True)
        self._pressed.emit()


class StopColls(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout_v = LayoutVer()
        self.setLayout(layout_v)

        self.label = QLabel(Lng.sett_stopcolls)
        layout_v.addWidget(self.label)

        layout_v.addSpacerItem(QSpacerItem(0, 10))

        self.input = InputBase()
        self.input.insert(", ".join(JsonData.stop_colls))
        layout_v.addWidget(self.input)

    def get_stopcolls(self):
        text = self.input.text()
        return [i.strip() for i in text.split(",")]


class UpdaterWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.v_layout = LayoutVer()
        self.setLayout(self.v_layout)

        self.btn = Btn(Lng.download_update)
        self.btn.setFixedWidth(150)
        self.btn.mouseReleaseEvent = self.update_btn_cmd
        self.v_layout.addWidget(self.btn)

    def update_btn_cmd(self, e):
        self.task = Updater()
        self.btn.setText(Lng.wait_update)
        self.task.signals_.no_connection.connect(self.no_connection_win)
        self.task.signals_.finished_.connect(self.finalize)
        UThreadPool.pool.start(self.task)

    def finalize(self):
        self.btn.setText(Lng.download_update)

    def no_connection_win(self):
        cmd_ = lambda: self.btn.setText(Lng.download_update)

        QTimer.singleShot(1000, cmd_)
        OpenWins.smb(self)

    def no_connection_btn_style(self):
        cmd_ = lambda: self.btn.setText(Lng.download_update)

        self.btn.setText(Lng.no_connection)
        QTimer.singleShot(1500, cmd_)


class ShowFiles(QWidget):
    def __init__(self):
        super().__init__()

        self.v_layout = LayoutVer()
        self.setLayout(self.v_layout)

        self.btn = Btn(Lng.show_app_support)
        self.btn.setFixedWidth(150)
        self.btn.mouseReleaseEvent = self.btn_cmd
        self.v_layout.addWidget(self.btn)

    def btn_cmd(self, e):
        try:
            subprocess.Popen(["open", APP_SUPPORT_DIR])
        except Exception as e:
            print(e)


class RestoreBtn(Btn):
    _pressed = pyqtSignal()

    def __init__(self):
        super().__init__(Lng.restore_db)
        self.setFixedWidth(150)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        self._pressed.emit()
        setattr(self, "flag", True)
        return super().mouseReleaseEvent(ev)


class WinSettings(WinChild):
    def __init__(self):
        super().__init__()

        self.close_btn_cmd(self.cancel_cmd)
        self.min_btn_disable()
        self.max_btn_disable()
        self.set_titlebar_title(Lng.settings)

        QTimer.singleShot(10, self.init_ui)
        self.setFixedSize(420, 500)
        self.setFocus()

        self.new_coll_path = None
        self.new_lang = None
        self.need_reset = None

    def init_ui(self):
        self.change_lang = ChangeLang()
        self.change_lang._pressed.connect(lambda: self.ok_btn.setText(Lng.apply))
        self.content_lay_v.addWidget(self.change_lang)
        self.content_lay_v.addSpacerItem(QSpacerItem(0, 30))

        h_wid = QWidget()
        self.content_lay_v.addWidget(h_wid)
        h_layout = LayoutHor()
        h_wid.setLayout(h_layout)
        self.content_lay_v.addSpacerItem(QSpacerItem(0, 25))

        self.update_wid = UpdaterWidget()
        h_layout.addWidget(self.update_wid)

        show_files = ShowFiles()
        h_layout.addWidget(show_files)

        self.restore_db_btn = RestoreBtn()
        self.restore_db_btn._pressed.connect(lambda: self.ok_btn.setText(Lng.apply))
        self.content_lay_v.addWidget(self.restore_db_btn)
        self.content_lay_v.addSpacerItem(QSpacerItem(0, 30))

        self.stopcolls = StopColls()
        self.content_lay_v.addWidget(self.stopcolls)
        self.content_lay_v.addSpacerItem(QSpacerItem(0, 30))

        coll_folder_list_label = QLabel(text=Lng.where_to_look_coll_folder)
        self.content_lay_v.addWidget(coll_folder_list_label)
        self.content_lay_v.addSpacerItem(QSpacerItem(0, 10))

        self.coll_folder_list_input = CollFolderListInput()
        self.content_lay_v.addWidget(self.coll_folder_list_input)
        self.content_lay_v.addSpacerItem(QSpacerItem(0, 30))

        self.content_lay_v.addStretch()

        btns_wid = QWidget()
        btns_layout = LayoutHor()
        btns_wid.setLayout(btns_layout)
        self.content_lay_v.addWidget(btns_wid)

        btns_layout.addStretch(1)

        self.ok_btn = Btn(Lng.ok)
        self.ok_btn.setFixedSize(90, self.ok_btn.height())
        self.ok_btn.mouseReleaseEvent = self.ok_cmd
        btns_layout.addWidget(self.ok_btn)

        btns_layout.addSpacerItem(QSpacerItem(10, 0))

        self.cancel_btn = Btn(Lng.cancel)
        self.cancel_btn.setFixedSize(90, self.cancel_btn.height())
        self.cancel_btn.mouseReleaseEvent = self.cancel_cmd
        btns_layout.addWidget(self.cancel_btn)

        btns_layout.addStretch(1)

    def cancel_cmd(self, *args):
        self.close()

    def ok_cmd(self, e):
        coll_folder_list = self.coll_folder_list_input.get_text()
        stop_colls = self.stopcolls.get_stopcolls()

        if hasattr(self.restore_db_btn, "flag"):
            print("settings win restore db")
            JsonData.write_json_data()
            QApplication.quit()

            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)

            if os.path.exists(HASH_DIR):
                shutil.rmtree(HASH_DIR)

            Utils.start_new_app()

        elif hasattr(self.change_lang, "flag"):
            print("settings win change lang")
            JsonData.write_json_data()
            QApplication.quit()
            Utils.start_new_app()

        elif stop_colls != JsonData.stop_colls:
            print("settings win stop colls updated")
            JsonData.stop_colls = stop_colls
            Scaner.app.stop()
            Scaner.app.start()
            JsonData.write_json_data()

        elif coll_folder_list != JsonData.coll_folder_list:
            print("settings win coll folder list updated")
            JsonData.coll_folder_list = coll_folder_list
            Scaner.app.stop()
            Scaner.app.start()
            JsonData.write_json_data()

        self.close()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.close()

        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd(a0)
        return super().keyPressEvent(a0)
