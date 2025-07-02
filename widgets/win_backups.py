import json
import os
import shutil
from typing import Literal

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QApplication, QLabel, QListWidget,
                             QListWidgetItem, QPushButton, QSpacerItem,
                             QWidget)

from cfg import Static
from system.lang import Lang
from system.main_folder import MainFolder
from system.filters import UserFilter
from system.utils import MainUtils

from ._base_widgets import (SvgBtn, UHBoxLayout, UMenu, UTextEdit, UVBoxLayout,
                            WinSystem)
from .actions import OpenInView


class ViewBackupWin(WinSystem):
    def __init__(self, dir_item = os.DirEntry):
        super().__init__()
        self.dir_item = dir_item
        self.central_layout.setSpacing(0)
        self.setWindowTitle(self.dir_item.name)

        with open(self.dir_item.path, "r", encoding="utf-8") as f:
            json_data: dict = json.load(f)
            validated = MainFolder.validate(json_data)
            main_folder_list = [
                MainFolder.from_model(m)
                for m in validated.main_folder_list
            ]

        text_edit = UTextEdit()
        self.central_layout.addWidget(text_edit)
        
        general_rows = []
        for main_folder in main_folder_list:
            rows = [
                main_folder.name,
                *main_folder.paths,
                *main_folder.stop_list,
            ]
            for i in rows:
                general_rows.append(i)
            general_rows.append("\n")
        text_edit.setText("\n".join(general_rows))

        self.setFixedSize(400, 400)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)


class UListWidgetItem(QListWidgetItem):
    hh = 25

    def __init__(self, parent: QListWidget):
        super().__init__(parent)
        self.setSizeHint(QSize(parent.width(), self.hh))


class ULabel(QLabel):
    def __init__(self, dir_item: os.DirEntry):
        super().__init__()
        self.dir_item = dir_item
        self.setText(self.dir_item.name)
        self.setStyleSheet("padding-left: 2px;")

    def open_view_win(self):
        self.view_win = ViewBackupWin(self.dir_item)
        self.view_win.adjustSize()
        self.view_win.center_relative_parent(self.window())
        self.view_win.show()

    def mouseDoubleClickEvent(self, a0):
        self.open_view_win()
        return super().mouseDoubleClickEvent(a0)
    
    def contextMenuEvent(self, ev):
        self.cont_menu = UMenu(ev)

        view = OpenInView(self.cont_menu)
        view._clicked.connect(self.open_view_win)
        self.cont_menu.addAction(view)

        self.cont_menu.show_()

        return super().contextMenuEvent(ev)


class WinBackups(WinSystem):
    list_item_h = 25
    main_folders_type = "main_folders"
    user_filters_type = "user_filters"

    def __init__(self, type: Literal["main_folders", "user_filters"]):
        super().__init__()
        self.type = type

        self.central_layout.setContentsMargins(10, 10, 10, 10)
        self.central_layout.setSpacing(10)
        self.init_ui()
        self.setFixedSize(350, 400)

    def init_ui(self):
        descr = QLabel("Выберите резервную копию")
        self.central_layout.addWidget(descr)

        self.list_widget = QListWidget(self)
        self.list_widget.horizontalScrollBar().setDisabled(True)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.central_layout.addWidget(self.list_widget)

        backups = self.get_backup_list()
        validated_list = self.validate_backup_list(backups)
        validated_list = sorted(validated_list, key=lambda d: d.stat().st_mtime, reverse=True)

        for dir_item in validated_list:
            item = UListWidgetItem(self.list_widget)
            label = ULabel(dir_item)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, label)

        apply_btn = QPushButton(text=Lang.apply)
        apply_btn.setFixedWidth(90)
        apply_btn.clicked.connect(self.apply_cmd)
        self.central_layout.addWidget(apply_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setFocus()

    def validate_backup_list(self, backup_list: os.DirEntry) -> list[os.DirEntry]:
        validated_list: list[os.DirEntry] = []

        for i in backup_list:
            try:
                with open(i.path, "r", encoding="utf-8") as f:
                    json_data: dict = json.load(f)

                    if self.type == self.main_folders_type:
                        MainFolder.validate(json_data)
                    else:
                        UserFilter.validate(json_data)

                    validated_list.append(i)
            except Exception as e:
                continue

        return validated_list

    def get_backup_list(self) -> list[os.DirEntry]:
        return [
            i
            for i in os.scandir(Static.APP_SUPPORT_BACKUP)
            if self.type in i.name
        ]
    
    def apply_cmd(self):
        item = self.list_widget.currentItem()

        if item is None:
            return

        u_label: ULabel = self.list_widget.itemWidget(item)
        dir_item = u_label.dir_item

        if self.type == self.main_folders_type:
            old_file = MainFolder.json_file
        else:
            old_file = UserFilter.json_file

        os.remove(old_file)
        shutil.copyfile(dir_item.path, old_file)

        self.hide()

        QApplication.quit()
        MainUtils.start_new_app()
    
    def closeEvent(self, a0):
        # a0.ignore()
        ...