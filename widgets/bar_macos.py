import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QContextMenuEvent, QImage, QKeyEvent, QPixmap
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QMenuBar, QSpacerItem, QHBoxLayout

from cfg import JsonData, Static
from system.items import SettingsItem
from system.lang import Lng
from system.utils import Utils

from ._base_widgets import (SelectableLabel, TransparentLabel, UMainWidget,
                            UMenu, TransparentWidget, UPushButton, UGroupBox)
from .win_servers import ServersWin
from .win_settings import WinSettings


class AboutWin(UMainWidget):
    icon_path = Static.APP_ICONS / "icon.png"
    icon_size = 100

    INFO_TEXT = "\n".join([
        f"Version {Static.APP_VERSION}",
        "Developed by Evlosh",
        "email: evlosh@gmail.com",
        "telegram: evlosh",
    ])

    def __init__(self):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Static.APP_NAME)
        self.central_layout.setSpacing(5)
        self.central_layout.setContentsMargins(10, 0, 10, 10)

        h_container = TransparentWidget()
        self.central_layout.addWidget(h_container)
        h_layout = QHBoxLayout(h_container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(5)

        icon = TransparentLabel()
        qimage = QImage(str(self.icon_path))
        qimage_saled = Utils.qimage_scaled_high_dpi(qimage, self.icon_size)
        icon.setPixmap(QPixmap.fromImage(qimage_saled))
        h_layout.addWidget(icon)

        lbl = SelectableLabel(self.INFO_TEXT)
        h_layout.addWidget(lbl)

        close_btn = UPushButton(Lng.close[JsonData.lng_index])
        self.central_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        close_btn.clicked.connect(self.deleteLater)
        close_btn.setFixedWidth(150)
        self.adjustSize()

        if not self.icon_path.exists():
            print("bar macos icon png not exists")

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        """Закрывает окно по Escape или Enter."""
        if a0.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return):
            self.deleteLater()


class BarMacos(QMenuBar):
    def __init__(self):
        super().__init__()
        self.mainMenu = UMenu(Lng.menu[JsonData.lng_index], self)

        # Добавили self. к действию подключения к серверу
        self.server_win = QAction(Lng.connect_to_server[JsonData.lng_index], self)
        self.server_win.triggered.connect(self.open_server_window)
        self.mainMenu.addAction(self.server_win)

        # Добавили self. к действию настроек
        self.actionSettings = QAction(Lng.open_settings_window[JsonData.lng_index], self)
        self.actionSettings.triggered.connect(self.open_settings_window)
        self.mainMenu.addAction(self.actionSettings)

        self.mainMenu.addSeparator()

        # Добавили self. к действию "О программе"
        self.actionAbout = QAction(Lng.show_about[JsonData.lng_index], self)
        self.actionAbout.setMenuRole(QAction.MenuRole.NoRole)
        self.actionAbout.triggered.connect(self.open_about_window)
        self.mainMenu.addAction(self.actionAbout)

        self.addMenu(self.mainMenu)
        self.setNativeMenuBar(True)

    def open_server_window(self):
        self.server_win = ServersWin()
        self.server_win.center_to_parent(self.window())
        self.server_win.show()

    def open_settings_window(self):
        item = SettingsItem("general", "")
        self.settings_win = WinSettings(item)
        self.settings_win.center_to_parent(self.window())
        self.settings_win.show()

    def open_about_window(self):
        self.about_win = AboutWin()
        self.about_win.center_to_parent(self.window())
        self.about_win.show()
