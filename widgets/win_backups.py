import os
from typing import Literal

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QLabel, QListWidget, QListWidgetItem, QPushButton,
                             QSpacerItem, QWidget)

from cfg import Static
from system.lang import Lang
from system.main_folder import MainFolder
import json
from ._base_widgets import (SvgBtn, UHBoxLayout, UTextEdit, UVBoxLayout,
                            WinSystem)


class ViewBackupWin(WinSystem):
    def __init__(self, parent = None):
        super().__init__(parent)



class UListWidgetItem(QListWidgetItem):
    hh = 25

    def __init__(self, parent: QListWidget, dir_item: os.DirEntry):
        super().__init__(parent)
        self.setSizeHint(QSize(parent.width(), self.hh))
        self.dir_item = dir_item

    def open_view_win(self):
        ...

class WinBackups(WinSystem):
    list_item_h = 25

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

        list_widget = QListWidget(self)
        list_widget.horizontalScrollBar().setDisabled(True)
        list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.central_layout.addWidget(list_widget)

        backups = self.get_backup_list()
        validated_list = self.validate_backup_list(backups)
        validated_list = sorted(validated_list, key=lambda d: d.stat().st_mtime, reverse=True)

        for dir_item in validated_list:
            item = UListWidgetItem(list_widget, dir_item)
            label = QLabel(dir_item.name)
            label.setStyleSheet("padding-left: 2px;")
            list_widget.addItem(item)
            list_widget.setItemWidget(item, label)

        ok_btn = QPushButton(text=Lang.ok)
        ok_btn.setFixedWidth(90)
        ok_btn.clicked.connect(self.close)
        self.central_layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setFocus()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.deleteLater()

    def validate_backup_list(self, backup_list: os.DirEntry) -> list[os.DirEntry]:
        validated_list: list[os.DirEntry] = []

        for i in backup_list:
            try:
                with open(i.path, "r", encoding="utf-8") as f:
                    json_data: dict = json.load(f)
                    MainFolder.validate(json_data)
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