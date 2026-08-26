import os
import re
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QVBoxLayout

from cfg import JsonData, Static
from system.lang import Lng
from system.main_folder import Mf
from system.tasks import URunnable, UThreadPool

from ._base_widgets import (ConfirmWindow, HSep, MfAliasWidget, MfPathWidget,
                            RowArrowWidget, SaveRowArrowWidget, UGroupBox,
                            UMainWidget, UMenu, UPushButton)


def restart_app():
    os.execl(sys.executable, sys.executable, *sys.argv)
    QApplication.exit(0)


class ZipTask(URunnable):

    class Sigs(QObject):
        error = pyqtSignal()
        finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.sigs = self.Sigs()

    def task(self):
        shutil.rmtree(Static.APP_DATA_DIR, ignore_errors=True)
        try:
            Static.APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
            dest = Path(shutil.copy(Static.MIUZ_ZIP, Static.APP_DATA_DIR))
            with ZipFile(dest, "r") as zip_ref:
                zip_ref.extractall(Static.APP_DATA_DIR)
            dest.unlink(missing_ok=True)
        except Exception as e:
            print(f"ZipTask critical error: {e}")
            self.sigs.error.emit()
            return
        self.sigs.finished.emit()



class FirstLoadWin(UMainWidget):
    rus_flag = Static.COMMON_ICONS / "rus_flag.svg"
    eng_flag = Static.COMMON_ICONS / "eng_flag.svg"
    language_svg = Static.COMMON_ICONS / "language.svg"
    miuz_svg = Static.COMMON_ICONS / "miuz.svg"
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
        # self.setFixedHeight(self.height())

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

    def change_language(self, value: int):
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
            lng_btn_icon = QIcon(str(self.rus_flag))
        else:
            lng_label_text = f"{Lng.app_lang[1]} ({Lng.app_lang[0]})"
            lng_btn_text = eng_action_text
            lng_btn_icon  = QIcon(str(self.eng_flag))

        # Сохраняем ссылку в self.lng_container
        self.lng_container = UGroupBox()
        self.central_layout.addWidget(self.lng_container)
        
        lng_layout = QHBoxLayout(self.lng_container)
        lng_layout.setContentsMargins(*RowArrowWidget.group_margings)
        lng_layout.setSpacing(10)

        lng_wid = RowArrowWidget(lng_label_text)
        lng_wid.set_left_icon(str(self.language_svg))
        lng_wid.hide_arrow()
        lng_layout.addWidget(lng_wid)

        lng_icons = (
            QIcon(str(self.rus_flag)),
            QIcon(str(self.eng_flag))
        )

        lng_menu = UMenu(None)
        for value in (0, 1):
            action = QAction(Lng.russian[value], lng_menu)
            action.setIcon(lng_icons[value])
            action.setIconVisibleInMenu(True)
            action.triggered.connect(lambda e, v=value: self.change_language(v))
            lng_menu.addAction(action)

        lng_btn = UPushButton(lng_btn_text)
        lng_btn.setFixedWidth(100)
        lng_btn.setMenu(lng_menu)
        lng_btn.setIcon(lng_btn_icon)
        lng_layout.addWidget(lng_btn)

        # self.lng_container.adjustSize()

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
        self.last_block_container = UGroupBox()
        self.central_layout.addWidget(self.last_block_container)

        last_block_layout = QVBoxLayout(self.last_block_container)
        last_block_layout.setContentsMargins(*RowArrowWidget.group_margings)
        last_block_layout.setSpacing(RowArrowWidget.group_spacing)

        if Static.MIUZ_ZIP.exists():
            self.copy_zip_widget = RowArrowWidget(
                Lng.miuz_diamonds[self.lng_index]
            )
            self.copy_zip_widget.set_left_icon(self.miuz_svg)
            self.copy_zip_widget.clicked.connect(
                lambda: self.copy_zip_cmd()
            )
            last_block_layout.addWidget(self.copy_zip_widget)

        self.save_widget = SaveRowArrowWidget(self.lng_index)
        self.save_widget.clicked.connect(lambda: self.save_cmd())
        last_block_layout.addWidget(self.save_widget)

    def copy_zip_cmd(self):

        def fin():
            JsonData.lng_index = self.lng_index
            JsonData.write_json_data()
            restart_app()

        self.copy_task = ZipTask()
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
