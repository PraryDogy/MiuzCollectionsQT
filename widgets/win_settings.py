import os
import subprocess
from collections import defaultdict

from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QAction, QApplication, QGroupBox, QLabel,
                             QListWidget, QListWidgetItem, QPushButton,
                             QSpacerItem, QTabWidget, QWidget)

from base_widgets import ContextCustom, CustomTextEdit, LayoutHor, LayoutVer
from base_widgets.input import ULineEdit
from base_widgets.wins import WinSystem
from cfg import JsonData, Static
from lang import Lang
from utils.updater import Updater
from utils.utils import UThreadPool, Utils
from brands import Brand
from .actions import OpenWins

WIN_SIZE = (430, 550)
NEED_REBOOT = "___need_reboot___"
STOP_COLLS = "STOP_COLLS"
COLL_FOLDERS = "COLL_FOLDERS"


class RebootableSettings(QGroupBox):
    apply = pyqtSignal()

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
        self.reset_btn.clicked.connect(self.reset_btn_cmd)
        sec_row_lay.addWidget(self.reset_btn)

        descr = QLabel(text=Lang.restore_db_descr)
        sec_row_lay.addWidget(descr)

        v_lay.addWidget(first_row_wid)
        v_lay.addWidget(sec_row_wid)

    def cmd_(self, wid: QWidget):
        self.apply.emit()
        setattr(wid, NEED_REBOOT, True)

    def reset_btn_cmd(self, *args):
        self.lang_btn.setDisabled(True)
        self.cmd_(wid=self.reset_btn)

    def lang_btn_cmd(self, *args):
        # костыль но что ж поделать
        if self.lang_btn.text() == "Русский":
            self.lang_btn.setText("English")
        else:
            self.lang_btn.setText("Русский")

        self.reset_btn.setDisabled(True)
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
        ...
        self.task = Updater()
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


class AddBrandWindow(WinSystem):
    clicked_ = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setFixedSize(300, 80)
        self.central_layout.setSpacing(10)

        self.text_edit = ULineEdit()
        self.text_edit.setPlaceholderText(Lang.paste_text)
        self.central_layout.addWidget(self.text_edit)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)

        h_lay = LayoutHor()
        h_lay.setSpacing(10)
        h_wid.setLayout(h_lay)

        h_lay.addStretch()

        ok_btn = QPushButton(text=Lang.ok)
        ok_btn.clicked.connect(self.ok_cmd)
        ok_btn.setFixedWidth(90)
        h_lay.addWidget(ok_btn)

        can_btn = QPushButton(text=Lang.cancel)
        can_btn.clicked.connect(self.close)
        can_btn.setFixedWidth(90)
        h_lay.addWidget(can_btn)

        h_lay.addStretch()

    def ok_cmd(self):
        text = self.text_edit.text().replace("\n", "").strip()

        if text:
            self.clicked_.emit(text)
            self.close()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.close()
        return super().keyPressEvent(a0)


class BrandList(QListWidget):
    h_ = 25
    changed = pyqtSignal()

    def __init__(self, brand: Brand, items: list[str]):
        super().__init__()
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.contextMenuEvent = self.list_item_context
        self.brand_instance = brand

        for i in items:
            item_ = QListWidgetItem(i)
            item_.setSizeHint(QSize(self.width(), BrandList.h_))
            item_.item_name = i
            self.addItem(item_)

    def list_item_context(self, ev):
        menu = ContextCustom(event=ev)

        add_item = QAction(parent=menu, text=Lang.add_)
        add_item.triggered.connect(self.add_item_cmd)
        menu.addAction(add_item)

        wid = self.itemAt(ev.pos())
        if wid:
            del_item = QAction(parent=menu, text=Lang.del_)
            del_item.triggered.connect(self.del_item_cmd)
            menu.addAction(del_item)

        menu.show_menu()

    def mouseReleaseEvent(self, e):
        wid = self.itemAt(e.pos())
        if not wid:
            self.clearSelection()

        return super().mouseReleaseEvent(e)

    def del_item_cmd(self):
        selected_item = self.currentItem()
        row = self.row(selected_item)
        self.takeItem(row)
        self.changed.emit()

    def get_items(self):
        return [
            self.item(i).text()
            for i in range(self.count())
        ]

    def add_item_cmd(self):
        win = AddBrandWindow()
        win.clicked_.connect(self.add_item_fin)
        win.center_relative_parent(parent=self.window())
        win.show()

    def add_item_fin(self, text: str):
        item_ = QListWidgetItem(text)
        item_.setSizeHint(QSize(self.width(), BrandList.h_))
        item_.item_name = text
        self.addItem(item_)
        self.changed.emit()


class StopColls(BrandList):
    def __init__(self, brand, items):
        super().__init__(brand, items)


class CollFolders(BrandList):
    def __init__(self, brand, items):
        super().__init__(brand, items)


class BrandSettings(QTabWidget):
    apply = pyqtSignal()
    h_ = 25

    def __init__(self):
        super().__init__()
        self.stop_colls_wid: dict[int, CustomTextEdit] = {}
        self.coll_folders_wid: dict[int, CustomTextEdit] = {}

        for brand in Brand.brands_list:
            wid = self.brand_sett_ui(brand=brand)
            self.addTab(wid, brand.name)

        self.setCurrentIndex(0)

    def brand_sett_ui(self, brand: Brand):
        wid = QWidget()
        v_lay = LayoutVer()
        v_lay.setSpacing(10)
        v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        wid.setLayout(v_lay)

        stop_colls_lbl = QLabel(Lang.sett_stopcolls)
        v_lay.addWidget(stop_colls_lbl)

        stop_colls_list = StopColls(brand=brand, items=brand.stop_colls)
        stop_colls_list.changed.connect(self.list_changed)
        v_lay.addWidget(stop_colls_list)

        coll_folders_label = QLabel(Lang.where_to_look_coll_folder)
        v_lay.addWidget(coll_folders_label)

        coll_folders_list = CollFolders(brand=brand, items=brand.coll_folders)
        coll_folders_list.changed.connect(self.list_changed)
        v_lay.addWidget(coll_folders_list)

        return wid
    
    def list_changed(self):
        self.apply.emit()
        setattr(self, NEED_REBOOT, True)


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
        self.central_layout.addWidget(self.rebootable_settings)

        self.smpl_sett = SimpleSettings()
        self.central_layout.addWidget(self.smpl_sett)

        self.brand_settings = BrandSettings()
        self.central_layout.addWidget(self.brand_settings)

        rb_sett_cmd = lambda: self.cmd_(wid=self.brand_settings)
        self.rebootable_settings.apply.connect(rb_sett_cmd)

        lock_rebootable = lambda: self.cmd_(wid=self.rebootable_settings)
        self.brand_settings.apply.connect(lock_rebootable)

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
        self.cancel_btn.clicked.connect(self.close)
        btns_layout.addWidget(self.cancel_btn)

        btns_layout.addStretch(1)

    def cmd_(self, wid: QWidget):
        wid.setDisabled(True)
        self.ok_btn.setText(Lang.apply)

    def ok_cmd(self, *args):

        if hasattr(self.rebootable_settings.reset_btn, NEED_REBOOT):
            JsonData.write_json_data()
            QApplication.quit()
            Utils.rm_rf(folder_path=Static.APP_SUPPORT_DIR)
            Utils.start_new_app()

        elif hasattr(self.rebootable_settings.lang_btn, NEED_REBOOT):
            JsonData.lang_ind += 1
            Lang.init()
            JsonData.write_json_data()
            QApplication.quit()
            Utils.start_new_app()

        elif hasattr(self.brand_settings, NEED_REBOOT):
            for i in self.findChildren(CollFolders):
                i.brand_instance.coll_folders = i.get_items()

            for i in self.findChildren(StopColls):
                i.brand_instance.stop_colls = i.get_items()

            JsonData.write_json_data()
            QApplication.quit()
            Utils.start_new_app()

        self.close()

    def new_row_list(self, wid: CustomTextEdit) -> list[str]:
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
