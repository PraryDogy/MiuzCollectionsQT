import os
import shutil
import subprocess

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QApplication, QGroupBox, QLabel, QPushButton,
                             QSpacerItem, QTabWidget, QTextEdit, QWidget)

from base_widgets import CustomInput, CustomTextEdit, LayoutHor, LayoutVer
from base_widgets.wins import WinChild
from cfg import APP_SUPPORT_DIR, BRANDS, DB_FILE, HASH_DIR, JsonData
from lang import Lang
from utils.updater import Updater
from utils.utils import UThreadPool, Utils

from .actions import OpenWins


class ChangeLang(QGroupBox):
    _pressed = pyqtSignal()

    def __init__(self):
        super().__init__()

        layout_h = LayoutHor()
        layout_h.setSpacing(15)
        self.setLayout(layout_h)

        self.lang_btn = QPushButton(text=Lang._lang_name)
        self.lang_btn.setFixedWidth(150)
        self.lang_btn.clicked.connect(self.lng_cmd)
        layout_h.addWidget(self.lang_btn)

        self.lang_label = QLabel(Lang.lang_label)
        layout_h.addWidget(self.lang_label)
          
    def lng_cmd(self, *args):
        JsonData.lang_ind += 1
        self._pressed.emit()
        Lang.init()
        self.lang_btn.setText(Lang._lang_name)
        setattr(self, "flag", True)


class SecondGroup(QGroupBox):
    def __init__(self):
        super().__init__()

        h_layout = LayoutHor()
        h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        h_layout.setSpacing(15)
        self.setLayout(h_layout)

        self.updater_btn = QPushButton(text=Lang.download_update)
        self.updater_btn.setFixedWidth(150)
        self.updater_btn.clicked.connect(self.update_btn_cmd)
        h_layout.addWidget(self.updater_btn)

        self.show_files_btn = QPushButton(text=Lang.show_app_support)
        self.show_files_btn.setFixedWidth(150)
        self.show_files_btn.clicked.connect(self.show_files_cmd)
        h_layout.addWidget(self.show_files_btn)

    def show_files_cmd(self, *args):
        try:
            subprocess.Popen(["open", APP_SUPPORT_DIR])
        except Exception as e:
            print(e)

    def update_btn_cmd(self, *args):
        self.task = Updater()
        self.updater_btn.setText(Lang.wait_update)
        self.task.signals_.no_connection.connect(self.no_connection_win)
        self.task.signals_.finished_.connect(self.finalize)
        UThreadPool.pool.start(self.task)

    def finalize(self):
        self.updater_btn.setText(Lang.download_update)

    def no_connection_win(self):
        cmd_ = lambda: self.updater_btn.setText(Lang.download_update)

        QTimer.singleShot(1000, cmd_)
        OpenWins.smb(self.window())

    def no_connection_btn_style(self):
        cmd_ = lambda: self.updater_btn.setText(Lang.download_update)

        self.updater_btn.setText(Lang.no_connection)
        QTimer.singleShot(1500, cmd_)


class CollFolderListInput(CustomTextEdit):
    def __init__(self, brand_ind: int):
        super().__init__()
        self.brand_ind = brand_ind

        self.setPlaceholderText("Коллекции, каждая с новой строки")
        self.setFixedHeight(130)
        self.setLineWrapMode(QTextEdit.NoWrap)
        h_bar = self.horizontalScrollBar()
        h_bar.setFixedHeight(0)

        text = "\n".join(JsonData.coll_folders[brand_ind])
        self.setText(text)

    def get_coll_folders_list(self):
        text = self.toPlainText()
        coll_folder_list = text.split("\n")

        coll_folder_list = [
            os.sep + i.strip().strip(os.sep)
            for i in coll_folder_list
            if i
            ]
        
        return coll_folder_list


class StopColls(QWidget):
    def __init__(self, brand_ind: int):
        super().__init__()
        self.brand_ind = brand_ind

        layout_v = LayoutVer()
        self.setLayout(layout_v)

        self.label = QLabel(Lang.sett_stopcolls)
        layout_v.addWidget(self.label)

        layout_v.addSpacerItem(QSpacerItem(0, 10))

        self.input = CustomInput()
        self.input.setPlaceholderText("Через запятую")
        self.input.insert(", ".join(JsonData.stop_colls[brand_ind]))
        layout_v.addWidget(self.input)

    def get_stopcolls(self):
        text = self.input.text()
        return [i.strip() for i in text.split(",")]


class BrandSett(QTabWidget):
    def __init__(self):
        super().__init__()
        self.stop_colls_wid: list[StopColls] = []
        self.coll_folders_wid: list[CollFolderListInput] = []

        for i in BRANDS:
            wid = self.ui(brand_ind=BRANDS.index(i))
            self.addTab(wid, i)

        self.setCurrentIndex(JsonData.brand_ind)

    def ui(self, brand_ind: int):
        wid = QWidget()
        v_lay = LayoutVer()
        wid.setLayout(v_lay)

        stopcolls = StopColls(brand_ind)
        v_lay.addWidget(stopcolls)
        v_lay.addSpacerItem(QSpacerItem(0, 30))
        self.stop_colls_wid.append(stopcolls)

        coll_folder_list_label = QLabel(text=Lang.where_to_look_coll_folder)
        v_lay.addWidget(coll_folder_list_label)
        v_lay.addSpacerItem(QSpacerItem(0, 10))

        collfolders = CollFolderListInput(brand_ind)
        v_lay.addWidget(collfolders)
        v_lay.addSpacerItem(QSpacerItem(0, 30))
        self.coll_folders_wid.append(collfolders)

        return wid
    

class RestoreBd(QGroupBox):
    clicked_ = pyqtSignal()

    def __init__(self):
        super().__init__()

        h_lay = LayoutHor()
        h_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setLayout(h_lay)

        self.restore_db_btn = QPushButton(Lang.restore_db)
        self.restore_db_btn.setFixedWidth(150)
        self.restore_db_btn.clicked.connect(self.cmd_)
        h_lay.addWidget(self.restore_db_btn)

    def cmd_(self, *args):
        setattr(self, "flag", True)
        self.clicked_.emit()


class WinSettings(WinChild):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(Lang.settings)

        QTimer.singleShot(10, self.init_ui)
        self.setFixedSize(420, 500)
        self.setFocus()

        self.new_coll_path = None
        self.new_lang = None
        self.need_reset = None

    def init_ui(self):
        self.content_lay_v.setSpacing(10)

        cmd_lang = lambda: self.ok_btn.setText(Lang.apply)
        self.change_lang = ChangeLang()
        self.change_lang._pressed.connect(cmd_lang)
        self.content_lay_v.addWidget(self.change_lang)

        self.second_group = SecondGroup()
        self.content_lay_v.addWidget(self.second_group)

        self.restore_bd = RestoreBd()
        self.restore_bd.clicked_.connect(self.ok_cmd)
        self.content_lay_v.addWidget(self.restore_bd)

        self.brand_sett = BrandSett()
        self.content_lay_v.addWidget(self.brand_sett)

        btns_wid = QWidget()
        btns_layout = LayoutHor()
        btns_wid.setLayout(btns_layout)
        self.content_lay_v.addWidget(btns_wid)

        btns_layout.addStretch(1)

        self.ok_btn = QPushButton(text=Lang.ok)
        self.ok_btn.setFixedWidth(90)
        self.ok_btn.clicked.connect(self.ok_cmd)
        btns_layout.addWidget(self.ok_btn)

        btns_layout.addSpacerItem(QSpacerItem(10, 0))

        self.cancel_btn = QPushButton(text=Lang.cancel)
        self.cancel_btn.setFixedWidth(90)
        self.cancel_btn.clicked.connect(self.cancel_cmd)
        btns_layout.addWidget(self.cancel_btn)

        btns_layout.addStretch(1)

    def cancel_cmd(self, *args):
        self.close()

    def ok_cmd(self, *args):
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

        for i in self.brand_sett.coll_folders_wid:
            coll_folders = i.get_coll_folders_list()

            if coll_folders != JsonData.coll_folders[i.brand_ind]:
                setattr(self, "restart", True)
                JsonData.coll_folders[i.brand_ind] = coll_folders

        for i in self.brand_sett.stop_colls_wid:
            stop_colls = i.get_stopcolls()

            if stop_colls != JsonData.stop_colls[i.brand_ind]:
                setattr(self, "restart", True)
                JsonData.stop_colls[i.brand_ind] = stop_colls

        if hasattr(self, "restart"):
            JsonData.write_json_data()
            QApplication.quit()
            Utils.start_new_app()

        self.close()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.close()

        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd(a0)
        return super().keyPressEvent(a0)
