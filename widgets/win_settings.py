import os
import shutil
import subprocess

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QApplication, QGroupBox, QLabel, QPushButton,
                             QSpacerItem, QTabWidget, QWidget)

from base_widgets import CustomInput, CustomTextEdit, LayoutHor, LayoutVer
from base_widgets.wins import WinSystem
from cfg import JsonData, Static
from lang import Lang
from utils.updater import SimpleSettings
from utils.utils import UThreadPool, Utils

from .actions import OpenWins

WIN_SIZE = (430, 550)
NEED_REBOOT = "___need_reboot___"


class RebootableSettings(QGroupBox):
    apply_settings = pyqtSignal()

    def __init__(self):
        super().__init__()

        v_lay = LayoutVer()
        self.setLayout(v_lay)

        first_row_wid = QWidget()
        first_row_lay = LayoutHor()
        first_row_lay.setSpacing(15)
        first_row_wid.setLayout(first_row_lay)

        self.lang_btn = QPushButton(text=Lang._lang_name)
        self.lang_btn.setFixedWidth(150)
        self.lang_btn.clicked.connect(self.lang_btn_cmd)
        first_row_lay.addWidget(self.lang_btn)

        self.lang_label = QLabel(Lang.lang_label)
        first_row_lay.addWidget(self.lang_label)

        sec_row_wid = QWidget()
        sec_row_lay = LayoutHor()
        sec_row_lay.setSpacing(15)
        sec_row_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        sec_row_wid.setLayout(sec_row_lay)

        self.reset_btn = QPushButton(Lang.reset_all)
        self.reset_btn.setFixedWidth(150)
        self.reset_btn.clicked.connect(lambda: self.cmd_(wid=self.reset_btn))
        sec_row_lay.addWidget(self.reset_btn)

        descr = QLabel(text=Lang.restore_db_descr)
        sec_row_lay.addWidget(descr)

        v_lay.addWidget(first_row_wid)
        v_lay.addWidget(sec_row_wid)

    def cmd_(self, wid: QWidget):
        self.apply_settings.emit()
        setattr(wid, NEED_REBOOT, True)

    def lang_btn_cmd(self, *args):
        # костыль но что ж поделать
        if self.lang_btn.text() == "Русский":
            self.lang_btn.setText("English")
        else:
            self.lang_btn.setText("Русский")

        self.cmd_(wid=self.lang_btn)


class SimpleSettings(QGroupBox):
    def __init__(self):
        super().__init__()

        v_lay = LayoutVer()
        self.setLayout(v_lay)

        first_row_wid = QWidget()
        v_lay.addWidget(first_row_wid)
        first_row_lay = LayoutHor()
        first_row_lay.setSpacing(15)
        first_row_wid.setLayout(first_row_lay)

        self.updater_btn = QPushButton(text=Lang.download_update)
        self.updater_btn.setFixedWidth(150)
        self.updater_btn.clicked.connect(self.updater_btn_cmd)
        first_row_lay.addWidget(self.updater_btn)

        self.descr = QLabel(text=Lang.update_descr)
        first_row_lay.addWidget(self.descr)

        sec_row_wid = QWidget()
        v_lay.addWidget(sec_row_wid)
        sec_row_lay = LayoutHor()
        sec_row_lay.setSpacing(15)
        sec_row_wid.setLayout(sec_row_lay)

        self.show_files_btn = QPushButton(text=Lang.show_app_support)
        self.show_files_btn.setFixedWidth(150)
        self.show_files_btn.clicked.connect(self.show_files_cmd)
        sec_row_lay.addWidget(self.show_files_btn)

        self.lang_label = QLabel(Lang.show_files)
        sec_row_lay.addWidget(self.lang_label)

    def show_files_cmd(self, *args):
        try:
            subprocess.Popen(["open", Static.APP_SUPPORT_DIR])
        except Exception as e:
            print(e)

    def updater_btn_cmd(self, *args):
        self.task = SimpleSettings()
        self.updater_btn.setText(Lang.wait_update)
        self.task.signals_.no_connection.connect(self.updater_btn_smb)
        self.task.signals_.finished_.connect(self.updater_btn_cmd_fin)
        UThreadPool.pool.start(self.task)

    def updater_btn_cmd_fin(self):
        self.updater_btn.setText(Lang.download_update)

    def updater_btn_smb(self):
        cmd_ = lambda: self.updater_btn.setText(Lang.download_update)
        QTimer.singleShot(1000, cmd_)
        OpenWins.smb(self.window())


class BrandSettings(QTabWidget):
    _apply_settings = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.stop_colls_wid: dict[int, CustomTextEdit] = {}
        self.coll_folders_wid: dict[int, CustomTextEdit] = {}

        for i in Static.BRANDS:
            wid = self.brand_sett_ui(brand_ind=Static.BRANDS.index(i))
            self.addTab(wid, i)

        self.setCurrentIndex(JsonData.brand_ind)

    def brand_sett_ui(self, brand_ind: int):
        wid = QWidget()
        v_lay = LayoutVer()
        v_lay.setSpacing(10)
        v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        wid.setLayout(v_lay)

        stop_colls_lbl = QLabel(Lang.sett_stopcolls)
        v_lay.addWidget(stop_colls_lbl)

        stop_colls = "\n".join(JsonData.stop_colls[brand_ind])
        stop_colls_inp = CustomTextEdit()
        stop_colls_inp.setPlaceholderText(Lang.from_new_row)
        stop_colls_inp.setPlainText(stop_colls)
        stop_colls_inp.textChanged.connect(self.text_changed)
        v_lay.addWidget(stop_colls_inp)


        coll_folders_lbl = QLabel(text=Lang.where_to_look_coll_folder)
        v_lay.addWidget(coll_folders_lbl)

        coll_folders = "\n".join(JsonData.coll_folders[brand_ind])
        coll_folders_inp = CustomTextEdit()
        coll_folders_inp.setPlaceholderText(Lang.from_new_row)
        coll_folders_inp.setPlainText(coll_folders)
        coll_folders_inp.textChanged.connect(self.text_changed)
        v_lay.addWidget(coll_folders_inp)

        self.stop_colls_wid[brand_ind] = stop_colls_inp
        self.coll_folders_wid[brand_ind] = coll_folders_inp
    
        return wid
    
    def text_changed(self):
        self._apply_settings.emit()
        setattr(self, NEED_REBOOT, True)
    
    def get_stopcolls(self, wid: CustomInput):
        return [
            i.strip()
            for i in wid.text().split(",")
            if i
            ]

    def get_collfolders(self, wid: CustomTextEdit):
        return [
            os.sep + i.strip().strip(os.sep)
            for i in wid.toPlainText().split("\n")
            if i
            ]


class WinSettings(WinSystem):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lang.settings)

        QTimer.singleShot(10, self.init_ui)
        self.setFixedSize(*WIN_SIZE)
        self.setFocus()

    def init_ui(self):
        self.central_layout.setSpacing(10)

        self.rebootable_settings = RebootableSettings()
        self.rebootable_settings.apply_settings.connect(self.ok_to_apply)
        self.central_layout.addWidget(self.rebootable_settings)

        self.simple_settings = SimpleSettings()
        self.central_layout.addWidget(self.simple_settings)

        self.brand_sett = BrandSettings()
        self.brand_sett._apply_settings.connect(self.ok_to_apply)
        self.central_layout.addWidget(self.brand_sett)

        btns_wid = QWidget()
        btns_layout = LayoutHor()
        btns_wid.setLayout(btns_layout)
        self.central_layout.addWidget(btns_wid)

        btns_layout.addStretch(1)

        self.ok_btn = QPushButton(text=Lang.ok)
        self.ok_btn.setFixedWidth(100)
        self.ok_btn.clicked.connect(self.ok_cmd)
        btns_layout.addWidget(self.ok_btn)

        btns_layout.addSpacerItem(QSpacerItem(10, 0))

        self.cancel_btn = QPushButton(text=Lang.cancel)
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self.cancel_cmd)
        btns_layout.addWidget(self.cancel_btn)

        btns_layout.addStretch(1)

    def ok_to_apply(self, *args):
        self.ok_btn.setText(Lang.apply)

    def cancel_cmd(self, *args):
        self.close()

    def ok_cmd(self, *args):

        if hasattr(self.rebootable_settings.reset_btn, NEED_REBOOT):

            JsonData.write_json_data()
            QApplication.quit()

            if os.path.exists(Static.DB_FILE):
                os.remove(Static.DB_FILE)

            if os.path.exists(Static.HASH_DIR):
                shutil.rmtree(Static.HASH_DIR)

            Utils.start_new_app()

        elif hasattr(self.rebootable_settings.lang_btn, NEED_REBOOT):
            JsonData.lang_ind += 1
            Lang.init()
            JsonData.write_json_data()
            QApplication.quit()
            Utils.start_new_app()

        elif hasattr(self.brand_sett, NEED_REBOOT):

            for brand_ind, wid in self.brand_sett.stop_colls_wid.items():
                stop_colls = self.setup_lined_text(wid=wid)
                JsonData.stop_colls[brand_ind] = stop_colls

            for brand_ind, wid in self.brand_sett.coll_folders_wid.items():
                coll_folders = self.setup_lined_text(wid=wid)
                coll_folders = [
                    os.sep + i.strip().strip(os.sep)
                    for i in coll_folders
                    if i
                ]
                JsonData.coll_folders[brand_ind] = coll_folders            

            JsonData.write_json_data()
            QApplication.quit()
            Utils.start_new_app()

        self.close()

    def setup_lined_text(self, wid: CustomTextEdit):
        return[
            i
            for i in wid.toPlainText().split("\n")
            if i
        ]

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.close()

        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd(a0)
        return super().keyPressEvent(a0)
