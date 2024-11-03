import os
import subprocess
import sys
import traceback


def catch_err(exc_type, exc_value, exc_traceback):

    ERROR_MSG = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    APP_NAME: str = "MiuzCollections"

    FILE_: str = os.path.join(
        os.path.expanduser("~"),
        "Library",
        "Application Support",
        APP_NAME + "QT",
        "error.txt"
        )

    with open(FILE_, "w")as f:
        f.write(ERROR_MSG)

    subprocess.run(["open", FILE_])


if os.path.exists("lib"): 
    #lib folder appears when we pack this project to .app with py2app
    plugin_path = "lib/python3.11/PyQt5/Qt5/plugins"
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path
    sys.excepthook = catch_err
    print(f"plugin path enabled")


from PyQt5.QtCore import QEvent, QObject
from PyQt5.QtWidgets import QApplication

from cfg import JsonData
from database import Dbase
from signals import SignalsApp
from styles import Themes
from win_main import WinMain


class App(QApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)

        self.installEventFilter(self)
        self.aboutToQuit.connect(lambda: SignalsApp.all.win_main_cmd.emit("exit"))

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a1.type() == QEvent.Type.ApplicationActivate:
            if hasattr(SignalsApp.all, "win_main_cmd"):
                SignalsApp.all.win_main_cmd.emit("show")
        return super().eventFilter(a0, a1)


app = App(sys.argv)
JsonData.init()
Dbase.init()
SignalsApp.init()
Themes.set_theme(JsonData.theme)
win_main = WinMain()
win_main.show()
app.exec_()