from PyQt5.QtGui import QContextMenuEvent, QMouseEvent
from PyQt5.QtWidgets import QAction, QMenu, QMenuBar, QLabel, QAction
from PyQt5.QtCore import Qt

from cfg import cnf
from signals import gui_signals_app

from ..win_settings import WinSettings
from base_widgets import WinSmallBase, ContextMenuBase
from utils import MainUtils

class Manager:
    win_settings = None


class SelectableLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)

        txt = "\n".join([
            f"{cnf.app_name}",
            f"Version {cnf.app_ver}",
            "Developed by Evlosh",
            "email: evlosh@gmail.com",
            "telegram: @evlosh",
            ])
        
        self.setText(txt)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

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



class MacMenuBar(QMenuBar):
    def __init__(self):
        super().__init__()
        self.settings_win = None
        gui_signals_app.reload_menubar.connect(self.reload_menubar)
        
        self.init_ui()

    def init_ui(self):

        # Создаем меню
        self.mainMenu = QMenu(cnf.lng.bar_menu, self)

        # Добавляем пункт "Открыть настройки"
        actionSettings = QAction(cnf.lng.open_settings_window, self)
        actionSettings.triggered.connect(self.open_settings_window)
        self.mainMenu.addAction(actionSettings)

        # Добавляем пункт "О приложении"
        actionAbout = QAction(cnf.lng.about_my_app, self)
        actionAbout.triggered.connect(self.open_about_window)
        self.mainMenu.addAction(actionAbout)

        # Добавляем меню в MacMenuBar
        self.addMenu(self.mainMenu)

        self.setNativeMenuBar(True)

    def open_settings_window(self):
        Manager.win_settings = WinSettings(self)
        Manager.win_settings.show()

    def open_about_window(self):
        self.about_win = WinSmallBase(close_func = lambda e: self.about_win.deleteLater())
        self.about_win.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.about_win.setFixedSize(250, 150)
        self.about_win.disable_min_max()
        self.about_win.content_layout.setContentsMargins(10, 10, 10, 10)
        self.about_win.set_title(cnf.lng.about_my_app)

        lbl = SelectableLabel(self.about_win)
        self.about_win.content_layout.addWidget(lbl)

        self.about_win.center_win(self)
        self.about_win.show()

    def reload_menubar(self):
        self.mainMenu.deleteLater()
        self.init_ui()
