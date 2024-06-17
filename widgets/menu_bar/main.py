import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QAction, QLabel, QMenu, QMenuBar, QSpacerItem

from base_widgets import ContextMenuBase, WinSmallBase
from cfg import cnf
from signals import gui_signals_app
from utils import MainUtils

from ..win_settings import WinSettings


class Manager:
    win_settings = None
    win_about = None


class SelectableLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)

        txt = "\n".join([
            f"Version {cnf.app_ver}",
            "Developed by Evlosh",
            "email: evlosh@gmail.com",
            "telegram: evlosh",
            ])
        
        self.setText(txt)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        context_menu = ContextMenuBase(ev)

        copy_text = QAction(parent=context_menu, text=cnf.lng.copy)
        copy_text.triggered.connect(self.copy_text_md)
        context_menu.addAction(copy_text)

        context_menu.addSeparator()

        select_all = QAction(parent=context_menu, text=cnf.lng.copy_all)
        select_all.triggered.connect(lambda: MainUtils.copy_text(self.text()))
        context_menu.addAction(select_all)

        context_menu.show_menu()

    def copy_text_md(self):
        MainUtils.copy_text(self.selectedText())


class AboutWin(WinSmallBase):
    def __init__(self, parent):
        super().__init__(close_func=lambda e: self.deleteLater())

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.disable_min_max()
        self.set_title(cnf.app_name)
        self.setFixedSize(280, 240)

        icon = QSvgWidget(os.path.join("icon", "icon.svg"))
        icon.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        icon.setFixedSize(150, 130)
        self.content_layout.addWidget(icon, alignment=Qt.AlignCenter)

        self.content_layout.addSpacerItem(QSpacerItem(0, 20))

        lbl = SelectableLabel(self)
        self.content_layout.addWidget(lbl)


class MacMenuBar(QMenuBar):
    def __init__(self):
        super().__init__()
        self.settings_win = None
        gui_signals_app.reload_menubar.connect(self.reload_menubar)
        
        self.init_ui()

    def init_ui(self):
        self.mainMenu = QMenu(cnf.lng.bar_menu, self)

        # Добавляем пункт "Открыть настройки"
        actionSettings = QAction(cnf.lng.open_settings_window, self)
        actionSettings.triggered.connect(self.open_settings_window)
        self.mainMenu.addAction(actionSettings)

        # Добавляем пункт "О приложении"
        actionAbout = QAction(cnf.lng.show_about, self)
        actionAbout.triggered.connect(self.open_about_window)
        self.mainMenu.addAction(actionAbout)

        # Добавляем меню в MacMenuBar
        self.addMenu(self.mainMenu)

        self.setNativeMenuBar(True)

    def open_settings_window(self):
        Manager.win_settings = WinSettings(self)
        Manager.win_settings.show()

    def open_about_window(self):
        win = AboutWin(self)
        Manager.win_about = win
        win.center_win(self)
        win.show()


    def reload_menubar(self):
        self.mainMenu.deleteLater()
        self.init_ui()
