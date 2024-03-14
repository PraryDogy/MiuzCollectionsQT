from PyQt5.QtCore import QObject, QTimer

from signals import utils_signals_app
from ..main_utils import MainUtils
from .thread import ScanerThread, Manager as ScanerThreadManager


class ScanerShedule(QObject):
    def __init__(self):
        super().__init__()
        smb_check_ms = 15000

        self.smb_wait_timer = QTimer(self)
        self.smb_wait_timer.setInterval(smb_check_ms)
        self.smb_wait_timer.timeout.connect(self.start_thread)
        
        self.thread_wait_timer = QTimer(self)
        self.thread_wait_timer.setInterval(smb_check_ms)
        self.thread_wait_timer.timeout.connect(self.wait_thread)

        self.scan_again_timer = QTimer(self)
        self.scan_again_timer.setInterval(10 * 60 * 1000)
        # self.scan_again_timer.setInterval(120 * 1000)
        self.scan_again_timer.setSingleShot(True)
        self.scan_again_timer.timeout.connect(self.wait_thread)

        utils_signals_app.scaner_start.connect(self.wait_thread)
        utils_signals_app.scaner_stop.connect(self.stop_thread)
        utils_signals_app.scaner_err.connect(self.wait_thread)

        self.scaner_thread = False

    def wait_thread(self):
        if not self.scaner_thread or not self.scaner_thread.isRunning():
            self.thread_wait_timer.stop()
            self.start_thread()

        else:
            print("scaner wait prev thread finished")
            self.thread_wait_timer.start()

    def start_thread(self):
        if not MainUtils.smb_check():
            print("scaner no smb, 15 sec wait")
            self.smb_wait_timer.start()

        else:
            print("scaner start from shedule")
            self.scaner_thread = ScanerThread()
            self.smb_wait_timer.stop()
            self.scaner_thread.start()
            self.scan_again_timer.start()

    def stop_thread(self):
        ScanerThreadManager.flag = False


scaner_app = ScanerShedule()
