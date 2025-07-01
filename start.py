import os
import subprocess
import sys
import traceback


class System_:

    @classmethod
    def catch_error_in_app(cls, exctype, value, tb) -> None:

        if exctype == RuntimeError:
            # в приложении мы игнорируем эту ошибку
            return

        ERROR = "".join(traceback.format_exception(exctype, value, tb))

        ABOUT = [
            "Отправьте это сообщение в telegram @evlosh",
            "или на почту loshkarev@miuz.ru"
        ]

        ABOUT = " ".join(ABOUT)

        STARS = "*" * 40


        SUMMARY_MSG = "\n".join([ERROR, STARS, ABOUT])
        
        script = "scripts/error_msg.scpt"
        subprocess.run(["osascript", script, SUMMARY_MSG])

    def catch_error_in_proj(exctype, value, tb):

        if exctype == RuntimeError:
            error_message = "".join(traceback.format_exception(exctype, value, tb))
            print(error_message)
        else:
            sys.__excepthook__(exctype, value, tb)

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


if System_.set_plugin_path():
    sys.excepthook = System_.catch_error_in_app
else:
    sys.excepthook = System_.catch_error_in_proj


from PyQt5.QtCore import QEvent, QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from cfg import JsonData, Static
from system.database import Dbase
from system.filters import UserFilter
from system.lang import Lang
from system.main_folder import MainFolder
from system.paletes import ThemeChanger
from system.utils import UThreadPool
from widgets.win_main import WinMain


class App(QApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)

        JsonData.init()
        Dbase.init()
        Lang.init()
        MainFolder.init()
        UserFilter.init()
        UThreadPool.init()
        ThemeChanger.init()


        JsonData.write_json_data()
        MainFolder.write_json_data()
        UserFilter.write_json_data()

        icon_path = os.path.join(Static.INNER_IMAGES, "icon.icns")
        icon = QIcon(icon_path)
        self.setWindowIcon(icon)

        self.win_main = WinMain(argv)
        self.win_main.center()
        self.win_main.show()

        self.installEventFilter(self)
        self.aboutToQuit.connect(lambda: self.win_main.on_exit())

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a1.type() == QEvent.Type.ApplicationActivate:
            self.win_main.show()
        return super().eventFilter(a0, a1)

app = App(sys.argv)
app.exec()
