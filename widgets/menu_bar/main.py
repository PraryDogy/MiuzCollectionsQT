from PyQt5.QtWidgets import QAction, QMenu, QMenuBar

from cfg import cnf
from signals import gui_signals_app

from ..win_settings import WinSettings


class Manager:
    win_settings = None


class MacMenuBar(QMenuBar):
    def __init__(self):
        super().__init__()
        self.settings_win = None
        gui_signals_app.reload_menubar.connect(self.reload_menubar)
        
        self.init_ui()

    def init_ui(self):

        # Создаем меню
        self.mainMenu = QMenu(cnf.lng.settings, self)

        # Добавляем пункт "Открыть настройки"
        actionSettings = QAction(cnf.lng.open_settings_window, self)
        actionSettings.triggered.connect(self.open_settings_window)
        self.mainMenu.addAction(actionSettings)

        # # Добавляем пункт "О приложении"
        # actionAbout = QAction(cnf.lng.about_my_app, self)
        # actionAbout.triggered.connect(self.open_about_window)
        # self.mainMenu.addAction(actionAbout)

        # Добавляем меню в MacMenuBar
        self.addMenu(self.mainMenu)

        self.setNativeMenuBar(True)

    def open_settings_window(self):
        Manager.win_settings = WinSettings()
        Manager.win_settings.show()

    def open_about_window(self):
        print("Opening About Window")

    def reload_menubar(self):
        self.mainMenu.deleteLater()
        self.init_ui()