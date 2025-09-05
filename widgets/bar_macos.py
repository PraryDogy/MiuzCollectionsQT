import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QAction, QLabel, QMenu, QMenuBar, QSpacerItem

from cfg import Cfg, Static
from system.lang import Lng
from system.utils import MainUtils

from ._base_widgets import UMenu, WinSystem
from .win_settings import WinSettings


class SelectableLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)

        txt = "\n".join([
            f"Version {Static.APP_VER}",
            "Developed by Evlosh",
            "email: evlosh@gmail.com",
            "telegram: evlosh",
            ])
        
        self.setText(txt)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        context_menu = UMenu(ev)

        copy_text = QAction(parent=context_menu, text=Lng.copy[Cfg.lng])
        copy_text.triggered.connect(self.copy_text_md)
        context_menu.addAction(copy_text)

        context_menu.addSeparator()

        select_all = QAction(parent=context_menu, text=Lng.copy_all[Cfg.lng])
        select_all.triggered.connect(lambda: MainUtils.copy_text(self.text()))
        context_menu.addAction(select_all)

        context_menu.show_()
        return super().contextMenuEvent(ev)

    def copy_text_md(self):
        MainUtils.copy_text(self.selectedText())


class AboutWin(WinSystem):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(Static.APP_NAME)
        self.setFixedSize(280, 240)

        icon = QSvgWidget()
        icon.load("./images/icon.svg")
        icon.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        icon.setFixedSize(150, 130)
        self.central_layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self.central_layout.addSpacerItem(QSpacerItem(0, 20))

        lbl = SelectableLabel(self)
        self.central_layout.addWidget(lbl)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return):
            self.deleteLater()


class BarMacos(QMenuBar):
    def __init__(self):
        super().__init__()
        self.settings_win = None
        self.init_ui()

    def init_ui(self):
        self.mainMenu = QMenu(Lng.menu[Cfg.lng], self)

        # Добавляем пункт "Открыть настройки"
        actionSettings = QAction(Lng.open_settings_window[Cfg.lng], self)
        actionSettings.triggered.connect(self.open_settings_window)
        self.mainMenu.addAction(actionSettings)

        # Добавляем пункт "О приложении"
        actionAbout = QAction(Lng.show_about[Cfg.lng], self)
        actionAbout.triggered.connect(self.open_about_window)
        self.mainMenu.addAction(actionAbout)

        # Добавляем меню в MacMenuBar
        self.addMenu(self.mainMenu)

        self.setNativeMenuBar(True)

    def open_settings_window(self):
        self.win_settings = WinSettings()
        self.win_settings.center_relative_parent(self.window())
        self.win_settings.show()

    def open_about_window(self):
        self.about_win = AboutWin()
        self.about_win.center_relative_parent(self.window())
        self.about_win.show()
