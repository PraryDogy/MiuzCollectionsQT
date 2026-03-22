import os
import sys
import traceback
from pathlib import Path

from PyQt5.QtCore import QEvent, QObject, Qt, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QDialog, QGroupBox, QHBoxLayout,
                             QLabel, QPushButton, QTextEdit, QVBoxLayout)
from typing_extensions import Literal

from cfg import Cfg, Static
from system.database import Dbase
from system.filters import Filters
from system.main_folder import Mf
from system.paletes import ThemeChanger
from system.servers import Servers
from system.tasks import UThreadPool
from widgets._base_widgets import WinManager
from widgets.win_main import WinMain
from widgets.win_settings import NewMfWin


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


class Lng:
    settings_title = (
        "Настройки",
        "Settings"
    )
    setup_app = (
        "Настроить приложение",
        "Configure Application"
    )
    description = (
        (
            "Приложение \"Collections\" позволяет индексировать и "
            "быстро просматривать изображения, что полезно на "
            "медленных сетевых дисках."
        ),
        (
            "The \"Collections\" app allows you to index and "
            "quickly browse images, which is especially useful "
            "for slow network drives."
        )
    )


class ClickableGroupBox(QGroupBox):
    def __init__(self, title: str, callback: callable):
        super().__init__()
        self.setFixedSize(150, 70)
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
    copy_preload_files = pyqtSignal()
    setup_new_mf = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(Lng.settings_title[Cfg.lng])
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        self.title_label = QLabel(Lng.description[Cfg.lng])
        self.title_label.setWordWrap(True)
        self.title_label.setFixedWidth(310)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.title_label)

        groups_layout = QHBoxLayout()
        groups_layout.setSpacing(10)

        self.group_app = ClickableGroupBox(
            Lng.setup_app[Cfg.lng],
            self.setup_app
        )
        groups_layout.addWidget(self.group_app)

        zip_file = os.listdir(Static.internal_files_dir)[0]
        zip_file = Path(Static.internal_files_dir) / zip_file
        self.preload = ClickableGroupBox(
            zip_file.stem, 
            self.preload_selected_cmd
        )
        groups_layout.addWidget(self.preload)

        layout.addLayout(groups_layout)
        self.adjustSize()

    def setup_app(self):
        self.hide()
        self.setup_new_mf.emit()
        self.deleteLater()

    def preload_selected_cmd(self):
        self.hide()
        self.copy_preload_files.emit()
        self.deleteLater()

    def closeEvent(self, a0):
        os._exit(1)
        return super().closeEvent(a0)
    
    def keyPressEvent(self, a0):
        a0.ignore()


class LanguageSelect(QDialog):
    closed_ = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Language / Язык")
        
        btn_layout = QHBoxLayout()
        self.setLayout(btn_layout)

        self.btn_ru = ClickableGroupBox(
            "Русский",
            lambda: self.select_lang(0)
        )
        self.btn_en = ClickableGroupBox(
            "English",
            lambda: self.select_lang(1)
        )
        
        btn_layout.addWidget(self.btn_ru)
        btn_layout.addWidget(self.btn_en)
        
        self.adjustSize()

    def select_lang(self, index):
        Cfg.lng = index
        self.closed_.emit()
        self.deleteLater()
    
    def closeEvent(self, a0):
        os._exit(1)
        return super().closeEvent(a0)
    
    def keyPressEvent(self, a0):
        a0.ignore()


class App(QApplication):
    def __init__(self, argv: list[Literal["noscan", ""]]) -> None:
        self.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        self.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
        super().__init__(argv)
        self.argv = argv
        self.start()

    def start(self):

        def json_to_app():
            Mf.mf_list.clear()
            objects = (Cfg, Mf, Servers, Filters)
            for i in objects:
                i.json_to_app()

        def setup_new_mf():
            new_mf_win = NewMfWin()
            new_mf_win.show()

        def copy_preload_files():
            Cfg.remake_external_dir()
            Cfg.copy_preloaded_zip()
            Cfg.write_json_data()

        def first_load_win():
            first_load = FirstLoad()
            first_load.copy_preload_files.connect(copy_preload_files)
            first_load.copy_preload_files.connect(self.start_app)
            first_load.setup_new_mf.connect(setup_new_mf)
            first_load.exec_()

        def lng_win():
            lng_win = LanguageSelect()
            lng_win.closed_.connect(first_load_win)
            lng_win.exec_()

        json_to_app()
        if not Cfg.check_files():
            lng_win()
        elif not Mf.mf_list:
            lng_win()
        elif Static.app_ver > Cfg.app_ver:
            print("we are here")
            Dbase.set_short_hash_unique()
            Cfg.app_ver = Static.app_ver
            Cfg.write_json_data()
            self.start()
        else:
            Dbase.init()

            
            Dbase.set_short_hash_unique()


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
