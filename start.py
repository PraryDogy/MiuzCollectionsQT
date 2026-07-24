import os
import sys
import traceback

from PyQt6.QtCore import QEvent, QObject
from PyQt6.QtWidgets import (QApplication, QDialog, QPushButton, QTextEdit,
                             QVBoxLayout)
from typing_extensions import Literal

from cfg import JsonData, Static
from system.database import Dbase
from system.filters import Filters
from system.main_folder import Mf
from system.paletes import ThemeChanger
from system.servers import Servers
from system.tasks import UThreadPool
from widgets._base_widgets import UMainWindow
from widgets.win_first_load import FirstLoadWin
from widgets.win_main import WinMain


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
        d.exec()

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
            plugin_path = f"lib/python{ver}/PyQt6/Qt5/plugins"
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path
            return True
        else:
            return False
    
    @classmethod
    def show_prints(cls):
        """показывает откуда принты"""
        import builtins
        import inspect
        _original_print = print
        def debug_print(*args, **kwargs):
            frame = inspect.currentframe().f_back
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            _original_print(f"[{filename}:{lineno}]", *args, **kwargs)
        builtins.print = debug_print


class App(QApplication):
    def __init__(self, argv: list[Literal["noscan", ""]]) -> None:
        super().__init__(argv)
        self.argv = argv
        self.validate()

    def validate(self):
        # валидация путей
        if not os.path.exists(Static.external_dir):
            os.makedirs(Static.external_dir)

        if not os.path.exists(Static.external_hashdir):
            os.makedirs(Static.external_hashdir)

        if not os.path.exists(Static.external_db):
            open(Static.external_db, "w")

        # конфиг
        if not os.path.exists(Static.external_json_data):
            JsonData.write_json_data()
            # валидация cfg
        # data = JsonData.validate()
        # if data:
        #     JsonData.json_to_app(data)
        JsonData.json_to_app()

        # фильтры
        if not os.path.exists(Static.external_filters):
            open(Static.external_filters, "w")
        data = Filters.validate_json()
        if data:
            Filters.json_to_app(data)

        # сервера
        if not os.path.exists(Static.external_servers):
            open(Static.external_filters, "w")
        data = Servers.validate_json()
        if data:
            Servers.json_to_app(data)

        # mf,самое важное
        if not os.path.exists(Static.external_mf):
            open(Static.external_mf, "w")
        data = Mf.validate_json()
        if data:
            Mf.json_to_app(data)
            Mf.current_mf = Mf.items[0]
            # инициация приложения
            Dbase.init()
            ThemeChanger.init()
            UThreadPool.init()
            self.create_app()
        else:
            self.first_load_win = FirstLoadWin()
            self.first_load_win.show()

    def create_app(self):
        self.win_main = WinMain(self.argv)
        self.win_main.center_screen()
        self.win_main.show()
        self.installEventFilter(self)
        self.aboutToQuit.connect(lambda: self.win_main.on_exit())
        # icon = QIcon(os.path.join(Static.internal_icons, "icon.png"))
        # self.setWindowIcon(icon)

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a1.type() == QEvent.Type.ApplicationActivate:
            for i in UMainWindow.win_list:
                i.raise_()
                i.show()
        return super().eventFilter(a0, a1)


if "print" in sys.argv:
    print("Включено отслеживание print")
    System_.show_prints()

if System_.set_plugin_path():
    sys.excepthook = System_.catch_error_in_app

if __name__ == "__main__":
    app = App(argv=sys.argv)
    app.exec()
