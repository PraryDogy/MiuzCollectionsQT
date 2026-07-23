import os
import sys

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
                             QMenu, QVBoxLayout, QWidget)

from cfg import Static
from widgets._base_widgets import RowArrowWidget, UMainWidget, UPushButton


class Lng:
    app_lang = (
        "Язык приложения",
        "Application language"
    )
    lang = (
        "Язык",
        "Language"
    )
    rus = (
        "Русский",
        "Russian"
    )
    eng = (
        "Английский",
        "English"
    )


import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QMenu, QWidget


class FirstLoadWin(UMainWidget):
    rus_flag = os.path.join(Static.internal_icons, "rus_flag.svg")
    eng_flag = os.path.join(Static.internal_icons, "eng_flag.svg")

    def __init__(self):
        super().__init__()
        self.resize(500, 500)
        self.central_layout.setContentsMargins(5, 5, 5, 5)
        self.central_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.lng_index = 0

        # Ссылка на контейнер, чтобы обновлять только его
        self.lng_container = None 
        self.init_ui()

    def remove_ui(self):
        """Безопасное и мгновенное удаление старого контейнера."""
        if self.lng_container is not None:
            self.central_layout.removeWidget(self.lng_container)
            self.lng_container.setParent(None)
            self.lng_container.deleteLater()
            self.lng_container = None

    def init_ui(self):
        self.init_lang_widget()

    def lng_action(self, value: int):
        if self.lng_index == value:
            return
        self.lng_index = value
        self.remove_ui()
        self.init_ui()

    def init_lang_widget(self):
        if self.lng_index == 0:
            lng_label_text = f"{Lng.app_lang[0]} ({Lng.app_lang[1]})"
        else:
            lng_label_text = f"{Lng.app_lang[1]} ({Lng.app_lang[0]})"

        rus_action_text = Lng.rus[self.lng_index]
        eng_action_text = Lng.eng[self.lng_index]
        lng_btn_text = rus_action_text if self.lng_index == 0 else eng_action_text

        # Сохраняем ссылку в self.lng_container
        self.lng_container = QGroupBox()
        self.central_layout.addWidget(self.lng_container)
        
        lng_layout = QHBoxLayout(self.lng_container)
        lng_layout.setContentsMargins(5, 5, 5, 5)
        lng_layout.setSpacing(0)

        lng_label = QLabel(lng_label_text)
        lng_layout.addWidget(lng_label)
        lng_layout.addStretch()

        lng_btn = UPushButton(lng_btn_text)
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


app = QApplication(sys.argv)
win = FirstLoadWin()
win.show()
app.exec()