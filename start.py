import os
import sys
import traceback

from PyQt5.QtWidgets import (QApplication, QDialog, QPushButton, QTextEdit,
                             QVBoxLayout)


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
        
        d = QDialog()
        d.setWindowTitle("Ошибка")
        l = QVBoxLayout(d)

        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText(SUMMARY_MSG)
        l.addWidget(txt)

        l.addWidget(QPushButton("Закрыть", clicked=d.close))
        d.resize(500, 400)
        d.setFocus()
        d.exec_()

    def catch_error_in_proj(exctype, value, tb):
        if exctype == RuntimeError:
            try:
                frame = traceback.extract_tb(tb)[0]
                frame = f"{frame.filename}, line {frame.lineno}"
            except Exception:
                frame = ""
            print("Обработан RuntimeError:", frame)
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

from cfg import cfg
from system.database import Dbase
from system.filters import Filters
from system.main_folder import Mf
from system.paletes import ThemeChanger
from system.tasks import UThreadPool
from widgets._base_widgets import WinManager
from widgets.win_main import WinMain


class App(QApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)

        cfg.initialize()
        Filters.init()
        Dbase.init()
        Mf.init()
        UThreadPool.init()
        ThemeChanger.init()

        icon_path = "./images/icon.icns"
        icon = QIcon(icon_path)
        self.setWindowIcon(icon)

        self.win_main = WinMain(argv)
        self.win_main.center_screen()
        self.win_main.show()

        self.installEventFilter(self)
        self.aboutToQuit.connect(lambda: self.win_main.on_exit())

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a1.type() == QEvent.Type.ApplicationActivate:
            for i in WinManager.win_list:
                i.raise_()
                i.show()
        return super().eventFilter(a0, a1)

app = App(sys.argv)
app.exec()
