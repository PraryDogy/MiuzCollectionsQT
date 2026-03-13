import os
import shutil
import sys
import traceback

from PyQt5.QtCore import QEvent, QObject, Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QDialog, QGroupBox, QHBoxLayout,
                             QLabel, QListWidget, QListWidgetItem, QPushButton,
                             QTextEdit, QVBoxLayout, QWidget)
from typing_extensions import Literal

from cfg import Static, cfg
from system.database import Dbase
from system.filters import Filters
from system.main_folder import Mf
from system.paletes import ThemeChanger
from system.tasks import UThreadPool
from widgets._base_widgets import WinManager
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


class ClickableGroupBox(QGroupBox):
    def __init__(self, title: str, callback: callable):
        super().__init__()
        self.setFixedWidth(200)
        self.callback = callback
        
        layout = QVBoxLayout(self)
        self.label = QLabel(title)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.callback()
        super().mousePressEvent(event)


class FirstLoad(QDialog):
    set_miuz = pyqtSignal()
    set_default = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Начальная настройка")
        self.setFixedSize(500, 200)

        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(5)

        self.group_app = ClickableGroupBox(
            "Настроить приложение", 
            self._setup_app
        )
        self.group_miuz = ClickableGroupBox(
            "Установить настройки для MIUZ Diamonds", 
            self.setup_miuz
        )

        main_layout.addWidget(self.group_app)
        main_layout.addWidget(self.group_miuz)

    def _setup_app(self):
        print("Настройка приложения...")
        self.deleteLater()

    def setup_miuz(self):
        self.set_miuz.emit()
        self.deleteLater()

    def closeEvent(self, a0):
        os._exit(1)
        return super().closeEvent(a0)


class App(QApplication):
    def __init__(self, argv: list[Literal["noscan", ""]]) -> None:
        self.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        self.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
        super().__init__(argv)
        self.argv = argv

        check_files = cfg.check_files()
        if not check_files:
            first_load = FirstLoad()
            first_load.set_miuz.connect(self.set_miuz)
            first_load.exec_()
            return

    def set_miuz(self):
        cfg.copy_files()
        os._exit(1)

    def setup_app(self):
        Filters.init()
        Dbase.init()
        Mf.init()
        
        ThemeChanger.init()
        UThreadPool.init()

        self.win_main = WinMain(self.argv)
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

# показывает откуда принты
# import builtins
# import inspect
# _original_print = print
# def debug_print(*args, **kwargs):
#     frame = inspect.currentframe().f_back
#     filename = frame.f_code.co_filename
#     lineno = frame.f_lineno
#     _original_print(f"[{filename}:{lineno}]", *args, **kwargs)
# builtins.print = debug_print

if __name__ == "__main__":
    if System_.set_plugin_path():
        sys.excepthook = System_.catch_error_in_app
    else:
        sys.excepthook = System_.catch_error_in_proj
    app = App(argv=sys.argv)
    app.exec()
