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
    win_about = None


class SelectableLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)

        txt = "\n".join([
            f"Version {cnf.app_ver}",
            "Developed by Evlosh",
            "email: evlosh@gmail.com",
            "telegram: @evlosh",
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
        Manager.win_about = WinSmallBase(close_func = lambda e: Manager.win_about.deleteLater())
        Manager.win_about.setWindowModality(Qt.WindowModality.ApplicationModal)
        Manager.win_about.setFixedSize(255, 150)
        Manager.win_about.disable_min_max()
        Manager.win_about.content_layout.setContentsMargins(10, 10, 10, 10)
        Manager.win_about.set_title(cnf.app_name)

        lbl = SelectableLabel(Manager.win_about)
        Manager.win_about.content_layout.addWidget(lbl)

        Manager.win_about.center_win(self)
        Manager.win_about.show()

    def reload_menubar(self):
        self.mainMenu.deleteLater()
        self.init_ui()
