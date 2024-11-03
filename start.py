import os
import sys
import traceback

from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton


def catch_err(exc_type, exc_value, exc_traceback):
    error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    error_dialog(error_message)


def error_dialog(error_message):
    error_dialog = QMessageBox()
    error_dialog.setIcon(QMessageBox.Critical)
    error_dialog.setWindowTitle("Error / Ошибка")

    tt = "\n".join(["Отправьте ошибку / Send error", "email: loshkarev@miuz.ru", "tg: evlosh"])
    error_dialog.setText(tt)
    error_dialog.setDetailedText(error_message)

    exit_button = QPushButton("Выход")
    exit_button.clicked.connect(QApplication.quit)
    error_dialog.addButton(exit_button, QMessageBox.ActionRole)

    error_dialog.exec_()


if os.path.exists("lib"): 
    #lib folder appears when we pack this project to .app with py2app
    ...
    plugin_path = "lib/python3.11/PyQt5/Qt5/plugins"
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path
    sys.excepthook = catch_err
    print()
    print(f"plugin path enabled")
    print()


import os
from typing import List

from PyQt5.QtCore import QEvent, QObject, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

# import app происходит только после активации os.environ plugin_path
from cfg import JsonData
from database import Dbase
from signals import SignalsApp
from styles import Themes
from win_main import WinMain


class App(QApplication):
    def __init__(self, argv: List[str]) -> None:
        super().__init__(argv)

        if os.path.basename(os.path.dirname(__file__)) != "Resources":
            self.setWindowIcon(QIcon(os.path.join("icon", "icon.icns")))

        self.installEventFilter(self)
        self.aboutToQuit.connect(lambda: SignalsApp.all.win_main_cmd.emit("exit"))

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a1.type() == QEvent.Type.ApplicationActivate:
            SignalsApp.all.win_main_cmd.emit("show")
        return super().eventFilter(a0, a1)


JsonData.check_app_dirs()
JsonData.read_json_data()
Themes.set_theme(JsonData.theme)
Dbase.init()
app = App(sys.argv)
SignalsApp.init()
win_main = WinMain()
win_main.show()
app.exec_()
