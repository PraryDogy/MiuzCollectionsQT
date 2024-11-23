import os
import shutil
import subprocess

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QSpacerItem,
                             QTextEdit, QWidget, QTabWidget)

from base_widgets import CustomTextEdit, CustomInput, LayoutHor, LayoutVer
from base_widgets.wins import WinChild
from cfg import APP_SUPPORT_DIR, DB_FILE, HASH_DIR, JsonData, BRANDS
from lang import Lang
from utils.scaner import Scaner
from utils.updater import Updater
from utils.utils import UThreadPool, Utils

from .actions import OpenWins


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

        self.lang_btn = QPushButton(text=Lang._lang_name)
        self.lang_btn.setFixedWidth(150)
        self.lang_btn.clicked.connect(self.lng_cmd)
        layout_h.addWidget(self.lang_btn)

        layout_h.addSpacerItem(QSpacerItem(10, 0))

        self.lang_label = QLabel(Lang.lang_label)
        layout_h.addWidget(self.lang_label)
          
    def lng_cmd(self, *args):
        JsonData.lang_ind += 1
        self._pressed.emit()
        Lang.init()
        self.lang_btn.setText(Lang._lang_name)
        setattr(self, "flag", True)


class StopColls(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout_v = LayoutVer()
        self.setLayout(layout_v)

        self.label = QLabel(Lang.sett_stopcolls)
        layout_v.addWidget(self.label)

        layout_v.addSpacerItem(QSpacerItem(0, 10))

        self.input = CustomInput()
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

        self.btn = QPushButton(text=Lang.download_update)
        self.btn.setFixedWidth(150)
        self.btn.clicked.connect(self.update_btn_cmd)
        self.v_layout.addWidget(self.btn)

    def update_btn_cmd(self, *args):
        self.task = Updater()
        self.btn.setText(Lang.wait_update)
        self.task.signals_.no_connection.connect(self.no_connection_win)
        self.task.signals_.finished_.connect(self.finalize)
        UThreadPool.pool.start(self.task)

    def finalize(self):
        self.btn.setText(Lang.download_update)

    def no_connection_win(self):
        cmd_ = lambda: self.btn.setText(Lang.download_update)

        QTimer.singleShot(1000, cmd_)
        OpenWins.smb(self)

    def no_connection_btn_style(self):
        cmd_ = lambda: self.btn.setText(Lang.download_update)

        self.btn.setText(Lang.no_connection)
        QTimer.singleShot(1500, cmd_)


class ShowFiles(QWidget):
    def __init__(self):
        super().__init__()

        self.v_layout = LayoutVer()
        self.setLayout(self.v_layout)

        self.btn = QPushButton(text=Lang.show_app_support)
        self.btn.setFixedWidth(150)
        self.btn.clicked.connect(self.btn_cmd)
        self.v_layout.addWidget(self.btn)

    def btn_cmd(self, *args):
        try:
            subprocess.Popen(["open", APP_SUPPORT_DIR])
        except Exception as e:
            print(e)


class RestoreBtn(QPushButton):
    _pressed = pyqtSignal()

    def __init__(self):
        super().__init__(text=Lang.restore_db)
        self.setFixedWidth(150)
        self.clicked.connect(self.cmd_)

    def cmd_(self, *args):
        self._pressed.emit()
        setattr(self, "flag", True)


class BrandSett(QTabWidget):
    def __init__(self):
        super().__init__()

        for i in BRANDS:
            wid = self.ui(brand_ind=BRANDS.index(i))
            self.addTab(wid, i)

        self.setCurrentIndex(JsonData.brand_ind)

    def ui(self, brand_ind: int):

        wid = QWidget()
        v_lay = LayoutVer()
        wid.setLayout(v_lay)

        self.stopcolls = StopColls()
        v_lay.addWidget(self.stopcolls)
        v_lay.addSpacerItem(QSpacerItem(0, 30))

        coll_folder_list_label = QLabel(text=Lang.where_to_look_coll_folder)
        v_lay.addWidget(coll_folder_list_label)
        v_lay.addSpacerItem(QSpacerItem(0, 10))

        self.coll_folder_list_input = CollFolderListInput()
        v_lay.addWidget(self.coll_folder_list_input)
        v_lay.addSpacerItem(QSpacerItem(0, 30))

        return wid


class WinSettings(WinChild):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(Lang.settings)

        QTimer.singleShot(10, self.init_ui)
        self.setFixedSize(420, 480)
        self.setFocus()

        self.new_coll_path = None
        self.new_lang = None
        self.need_reset = None

    def init_ui(self):
        self.change_lang = ChangeLang()
        self.change_lang._pressed.connect(lambda: self.ok_btn.setText(Lang.apply))
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
        self.restore_db_btn._pressed.connect(lambda: self.ok_btn.setText(Lang.apply))
        self.content_lay_v.addWidget(self.restore_db_btn)
        self.content_lay_v.addSpacerItem(QSpacerItem(0, 30))

        self.brand_sett = BrandSett()
        self.content_lay_v.addWidget(self.brand_sett)

        self.content_lay_v.addStretch()

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
        # coll_folder_list = self.coll_folder_list_input.get_text()
        # stop_colls = self.stopcolls.get_stopcolls()

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

        # elif stop_colls != JsonData.stop_colls:
        #     print("settings win stop colls updated")
        #     JsonData.stop_colls = stop_colls
        #     Scaner.app.stop()
        #     Scaner.app.start()
        #     JsonData.write_json_data()

        # elif coll_folder_list != JsonData.coll_folder_list:
        #     print("settings win coll folder list updated")
        #     JsonData.coll_folder_list = coll_folder_list
        #     Scaner.app.stop()
        #     Scaner.app.start()
        #     JsonData.write_json_data()

        self.close()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.close()

        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd(a0)
        return super().keyPressEvent(a0)
