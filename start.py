import os
import subprocess
import sys
import traceback


class System_:

    @classmethod
    def catch_error(cls, *args) -> None:

        STARS = "*" * 40
        ABOUT = "Отправьте это сообщение в telegram @evlosh или на почту loshkarev@miuz.ru"
        ERROR = traceback.format_exception(*args)

        SUMMARY_MSG = "\n".join([*ERROR, STARS, ABOUT])

        APP_NAME: str = "MiuzCollections" + "QT"

        APP_SUPPORT = os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Application Support"
            )

        FILE_: str = os.path.join(
            APP_SUPPORT,
            APP_NAME,
            "error.txt"
            )
        
        os.makedirs(APP_SUPPORT, exist_ok=True)

        with open(FILE_, "w")as f:
            f.write(SUMMARY_MSG)
            subprocess.run(["open", FILE_])

    @classmethod
    def set_plugin_path(cls) -> bool:
        #lib folder appears when we pack this project to .app with py2app
        if os.path.exists("lib"): 
            plugin_path = "lib/python3.11/PyQt5/Qt5/plugins"
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path
            return True
        else:
            return False
        
    @classmethod
    def set_excepthook(cls) -> None:
        sys.excepthook = cls.catch_error


if System_.set_plugin_path():
    System_.set_excepthook()


from PyQt5.QtCore import QEvent, QObject
from PyQt5.QtWidgets import QApplication

from cfg import JsonData
from database import Dbase
from signals import SignalsApp
from utils.utils import UThreadPool
from utils.scaner import Scaner
from widgets.win_main import WinMain


class App(QApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)

        self.installEventFilter(self)
        self.aboutToQuit.connect(lambda: SignalsApp.all_.win_main_cmd.emit("exit"))

        print("q application started")

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a1.type() == QEvent.Type.ApplicationActivate:
            if hasattr(SignalsApp.all_, "win_main_cmd"):
                SignalsApp.all_.win_main_cmd.emit("show")
        return super().eventFilter(a0, a1)


JsonData.init()
Dbase.init()

app = App(sys.argv)

UThreadPool.init()
SignalsApp.init()
Scaner.init()

win_main = WinMain()
win_main.center()
win_main.show()

app.exec()
