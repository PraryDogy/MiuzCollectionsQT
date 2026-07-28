import os
import re
import shutil
import sys
from zipfile import ZipFile

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QMouseEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QFileDialog, QGroupBox, QHBoxLayout,
                             QLabel, QMenu, QVBoxLayout, QWidget)

from cfg import JsonData, Static
from system.lang import Lng
from system.main_folder import Mf
from system.tasks import URunnable, UThreadPool

from ._base_widgets import (ConfirmWindow, MfAliasWidget, MfPathWidget,
                            RowArrowWidget, SaveRowArrowWidget,
                            SelectableLabel, ULineEdit, UMainWidget,
                            UPushButton, VListWidget, VListWidgetItem,
                            WarningWindow)


def restart_app():
    os.execl(sys.executable, sys.executable, *sys.argv)
    QApplication.exit(0)


class ZipTask(URunnable):

    class Sigs(QObject):
        error = pyqtSignal()
        finished = pyqtSignal()

    def __init__(self, zip_path: str):
        super().__init__()
        self.sigs = self.Sigs()
        self.zip_path: str = zip_path

    def task(self):
        try:
            shutil.rmtree(Static.external_dir)
        except Exception as e:
            self.sigs.error.emit()
            return
        os.makedirs(Static.external_dir, exist_ok=True)
        dest = shutil.copy(self.zip_path, Static.external_dir)

        with ZipFile(dest, "r") as zip_ref:
            zip_ref.extractall(Static.external_dir)

        try:
            os.remove(dest)
        except Exception as e:
            print("ZipTask remove zip file error", e)
            
        self.sigs.finished.emit()


class FirstLoadWin(UMainWidget):
    rus_flag = os.path.join(Static.common_icons, "rus_flag.svg")
    eng_flag = os.path.join(Static.common_icons, "eng_flag.svg")
    language_svg = os.path.join(Static.common_icons, "language.svg")
    miuz_svg = os.path.join(Static.common_icons, "miuz.svg")
    svg_size = 16
    ww = 440

    def __init__(self):
        super().__init__()
        self.setFixedWidth(self.ww)
        self.set_always_on_top()
        self.set_close_only()
        UThreadPool.init()
        self.central_layout.setContentsMargins(5, 7, 5, 10)
        self.central_layout.setSpacing(10)
        self.central_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.lng_index = 0
        self.margins = 3
        self.init_ui()
        self.adjustSize()
        self.setFixedHeight(self.height())

    def remove_ui(self):
        while self.central_layout.count():
            item = self.central_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def init_ui(self):
        self.setWindowTitle(Lng.settings[self.lng_index])
        self.init_lang_widget()
        self.init_mf_alias_widget()
        self.init_path_widget()
        self.init_last_block()

    def lng_action(self, value: int):
        if self.lng_index == value:
            return
        self.remove_ui()
        self.lng_index = value
        self.init_ui()

    def init_lang_widget(self):
        rus_action_text = Lng.rus[self.lng_index]
        eng_action_text = Lng.eng[self.lng_index]

        if self.lng_index == 0:
            lng_label_text = f"{Lng.app_lang[0]} ({Lng.app_lang[1]})"
            lng_btn_text = rus_action_text
            lng_btn_icon = QIcon(self.rus_flag)
        else:
            lng_label_text = f"{Lng.app_lang[1]} ({Lng.app_lang[0]})"
            lng_btn_text = eng_action_text
            lng_btn_icon  = QIcon(self.eng_flag)

        # Сохраняем ссылку в self.lng_container
        self.lng_container = QGroupBox()
        self.central_layout.addWidget(self.lng_container)
        
        lng_layout = QHBoxLayout(self.lng_container)
        lng_layout.setContentsMargins(5, 7, 5, 0)
        lng_layout.setSpacing(10)

        lng_icon = QSvgWidget()
        lng_icon.load(self.language_svg)
        lng_icon.setFixedSize(self.svg_size, self.svg_size)
        lng_layout.addWidget(lng_icon)

        lng_label = QLabel(lng_label_text)
        lng_layout.addWidget(lng_label)
        lng_layout.addStretch()

        lng_btn = UPushButton(lng_btn_text)
        lng_btn.setFixedWidth(100)
        lng_btn.setIcon(lng_btn_icon)
        lng_layout.addWidget(lng_btn)

        lng_menu = QMenu(lng_btn)
        lng_btn.setMenu(lng_menu)

        rus_icon = QIcon(self.rus_flag)
        rus_action = QAction(rus_icon, rus_action_text, lng_menu)
        rus_action.setIconVisibleInMenu(True)
        rus_action.triggered.connect(lambda e, val=0: self.lng_action(val))
        lng_menu.addAction(rus_action)

        eng_icon = QIcon(self.eng_flag)
        eng_action = QAction(eng_icon, eng_action_text, lng_menu)
        eng_action.setIconVisibleInMenu(True)
        eng_action.triggered.connect(lambda e, val=1: self.lng_action(val))
        lng_menu.addAction(eng_action)

        self.lng_container.adjustSize()

    def init_mf_alias_widget(self):
        self.mf_alias_widget = MfAliasWidget(self.lng_index)
        self.mf_alias_widget.changed.connect(
            lambda: self.save_widget.show_warning()
        )
        self.central_layout.addWidget(self.mf_alias_widget)

    def init_path_widget(self):

        def mf_path_changed():
            if self.path_widget.mf_path:
                basename = os.path.basename(self.path_widget.mf_path).capitalize()
                self.mf_alias_widget.line_edit.setText(basename)
            self.path_widget.mf_path
            self.save_widget.show_warning()

        self.path_widget = MfPathWidget(self.lng_index)
        self.path_widget.changed.connect(
            lambda: mf_path_changed()
        )
        self.central_layout.addWidget(self.path_widget)

    def init_last_block(self):
        self.last_block_container = QGroupBox()
        self.central_layout.addWidget(self.last_block_container)

        last_block_layout = QVBoxLayout(self.last_block_container)
        last_block_layout.setContentsMargins(5, 0, 5, 0)
        last_block_layout.setSpacing(0)

        if os.path.exists(Static.miuz_zip):
            self.copy_zip_widget = RowArrowWidget(
                Lng.miuz_diamonds[self.lng_index]
            )
            self.copy_zip_widget.set_left_icon(self.miuz_svg)
            self.copy_zip_widget.clicked.connect(
                lambda: self.copy_zip_cmd(Static.miuz_zip)
            )
            last_block_layout.addWidget(self.copy_zip_widget)

        self.save_widget = SaveRowArrowWidget(self.lng_index)
        self.save_widget.hide_sep()
        self.save_widget.clicked.connect(lambda: self.save_cmd())
        last_block_layout.addWidget(self.save_widget)

    def copy_zip_cmd(self, path: str):

        def fin():
            JsonData.lng_index = self.lng_index
            JsonData.write_json_data()
            restart_app()

        self.copy_task = ZipTask(path)
        self.copy_task.sigs.finished.connect(fin)
        self.hide()
        UThreadPool.start(self.copy_task)

    def save_cmd(self):

        def save_fin(mf_alias: str, mf_path: str):
            mf = Mf(
                mf_alias=mf_alias,
                mf_paths=[mf_path, ],
                mf_stop_list=[],
                mf_current_path=mf_path
            )
            Mf.items.clear()
            Mf.items.append(mf)
            Mf.write_json_data()
            JsonData.lng_index = self.lng_index
            JsonData.write_json_data()
            restart_app()

        mf_alias = self.mf_alias_widget.validate()
        mf_path = self.path_widget.validate()
        if mf_alias and mf_path:
            self.save_win = ConfirmWindow(
                Lng.save_text_long[self.lng_index], 300, 90
            )
            self.save_win.ok_clicked.connect(
                lambda: save_fin(mf_alias, mf_path)
            )
            self.save_win.center_to_parent(self.window())
            self.save_win.show()
