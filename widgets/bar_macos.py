import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QContextMenuEvent, QImage, QKeyEvent, QPixmap
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QMenuBar, QSpacerItem

from cfg import JsonData, Static
from system.items import SettingsItem
from system.lang import Lng
from system.utils import Utils

from ._base_widgets import (SelectableLabel, TransparentLabel, UMainWidget,
                            UMenu)
from .win_servers import ServersWin
from .win_settings import WinSettings


class AboutWin(UMainWidget):
    ww = 280
    icon_path = Static.APP_ICONS / "icon.png"
    icon_size = 150
    opacity = 0.85

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
        self.setFixedWidth(self.ww)
        self.central_layout.setContentsMargins(10, 0, 10, 10)

        icon = TransparentLabel()
        qimage = QImage(str(self.icon_path))
        qimage_saled = Utils.pyqt_scaled_high_dpi(qimage, self.icon_size)
        icon.setPixmap(QPixmap.fromImage(qimage_saled))
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(self.opacity) 
        icon.setGraphicsEffect(opacity_effect)
        self.central_layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self.central_layout.addSpacerItem(QSpacerItem(0, 10))

        lbl = SelectableLabel(self.INFO_TEXT)
        self.central_layout.addWidget(lbl)

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
