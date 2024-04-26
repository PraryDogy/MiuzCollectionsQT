import sys

from PyQt5.QtCore import QEvent, Qt, QTimer
from PyQt5.QtWidgets import QApplication

from cfg import cnf
from widgets import WinMain
from signals import utils_signals_app
from utils import MainUtils

class Manager:
    smb_win = None
    first_load_win = None


class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)

        self.setAttribute(Qt.AA_UseHighDpiPixmaps)
        self.setStyleSheet(
            f"""
            QLabel {{ color: white; }};
            """
            )

        self.main_win = WinMain()
        self.main_win.show()

        self.installEventFilter(self)
        self.aboutToQuit.connect(self.on_exit)

        self.after_start_timer = QTimer(self)
        self.after_start_timer.setSingleShot(True)
        self.after_start_timer.timeout.connect(self.after_start)
        self.after_start_timer.start(100)

    def eventFilter(self, obj, event: QEvent):
        if event.type() == QEvent.ApplicationActivate:
            self.main_win.show()
        return super().eventFilter(obj, event)
    
    def on_exit(self):
        geo = self.main_win.geometry()

        cnf.root_g.update(
            {"aw": geo.width(), "ah": geo.height()}
            )
        cnf.write_json_cfg()
        MainUtils.close_all_win()

        utils_signals_app.scaner_stop.emit()
        # utils_signals_app.watcher_stop.emit()

    def after_start(self):

        if cnf.first_load:
            from widgets.win_first_load import WinFirstLoad
            cnf.first_load = False
            Manager.first_load_win = WinFirstLoad()
            Manager.first_load_win.show()
            return

        if not MainUtils.smb_check():
            from widgets.win_smb import WinSmb

            Manager.smb_win = WinSmb()
            Manager.smb_win.show()

        utils_signals_app.scaner_start.emit()
        # utils_signals_app.watcher_start.emit()

        # from widgets.win_smb import WinSmb
        # Manager.smb_win = WinSmb()
        # Manager.smb_win.show()

app = App()
