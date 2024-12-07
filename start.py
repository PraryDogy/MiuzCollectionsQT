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
        
        script = "applescripts/error_msg.scpt"
        subprocess.run(["osascript", script, SUMMARY_MSG])

    @classmethod
    def set_plugin_path(cls) -> bool:
        #lib folder appears when we pack this project to .app with py2app
        if os.path.exists("lib"): 
            ver = f"{sys.version_info.major}.{sys.version_info.minor}"
            plugin_path = f"lib/python{ver}/PyQt5/Qt5/plugins"
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path
            return True
        else:
            return False
        
    @classmethod
    def set_excepthook(cls) -> None:
        sys.excepthook = cls.catch_error


if System_.set_plugin_path():
    System_.set_excepthook()
# System_.set_excepthook()


from PyQt5.QtCore import QEvent, QObject
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from cfg import JsonData, Static
from database import Dbase
from lang import Lang
from signals import SignalsApp
from utils.scaner import Scaner
from utils.utils import UThreadPool
from widgets.win_main import WinMain


class App(QApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)

        icon_path = os.path.join(Static.IMAGES, "icon.icns")
        icon = QIcon(icon_path)
        self.setWindowIcon(icon)

        self.installEventFilter(self)
        self.aboutToQuit.connect(lambda: SignalsApp.all_.win_main_cmd.emit("exit"))

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a1.type() == QEvent.Type.ApplicationActivate:
            if hasattr(SignalsApp.all_, "win_main_cmd"):
                SignalsApp.all_.win_main_cmd.emit("show")
        return super().eventFilter(a0, a1)


JsonData.init()
Dbase.init()
Lang.init()

app = App(sys.argv)

UThreadPool.init()
SignalsApp.init()
Scaner.init()

win_main = WinMain()
win_main.center()
win_main.show()

app.exec()
