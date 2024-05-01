from PyQt5.QtCore import QObject, QTimer

from cfg import cnf
from signals import utils_signals_app

from ..main_utils import MainUtils
from .thread import Manager as ScanerThreadManager
from .thread import ScanerThread


class ScanerShedule(QObject):
    def __init__(self):
        super().__init__()

        self.wait_timer = QTimer(self)
        self.wait_timer.setSingleShot(True)
        self.wait_timer.timeout.connect(self.prepare_thread)

        utils_signals_app.scaner_start.connect(self.prepare_thread)
        utils_signals_app.scaner_stop.connect(self.stop_thread)

        self.scaner_thread = None

    def prepare_thread(self):
        self.wait_timer.stop()

        if not MainUtils.smb_check():
            print("scaner no smb")
            self.wait_timer.start(15000)

        elif self.scaner_thread:
            print("scaner wait prev scaner finished")
            self.wait_timer.start(15000)

        else:
            print("scaner started")
            self.start_thread()

    def start_thread(self):
        self.scaner_thread = ScanerThread()
        self.scaner_thread.finished.connect(self.finalize_scan)
        self.scaner_thread.start()

    def stop_thread(self):
        print("scaner manualy stopep. You need emit scaner start signal")
        ScanerThreadManager.flag = False
        self.wait_timer.stop()

    def finalize_scan(self):
        try:
            self.scaner_thread.quit()
        except Exception as e:
            print("scaner finalze scan quit thread", e)

        self.scaner_thread = None
        self.wait_timer.start(cnf.scaner_minutes * 60 * 1000)

scaner_app = ScanerShedule()
