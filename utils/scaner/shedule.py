from PyQt5.QtCore import QObject, QTimer

from cfg import cnf
from signals import utils_signals_app

from ..main_utils import MainUtils
from .thread import Manager as ScanerThreadManager
from .thread import ScanerThread


class ScanerShedule(QObject):
    def __init__(self):
        super().__init__()
        self.smb_wait_timer = QTimer(self)
        self.smb_wait_timer.setInterval(15000)
        self.smb_wait_timer.setSingleShot(True)
        self.smb_wait_timer.timeout.connect(self.start_thread)
        
        self.thread_wait_timer = QTimer(self)
        self.thread_wait_timer.setInterval(15000)
        self.thread_wait_timer.setSingleShot(True)
        self.thread_wait_timer.timeout.connect(self.wait_thread)

        self.next_scan_timer = QTimer(self)
        self.next_scan_timer.setInterval(cnf.scaner_minutes * 60 * 1000)
        self.next_scan_timer.setSingleShot(True)
        self.next_scan_timer.timeout.connect(self.wait_thread)

        utils_signals_app.scaner_start.connect(self.wait_thread)
        utils_signals_app.scaner_stop.connect(self.stop_thread)
        utils_signals_app.scaner_err.connect(self.wait_thread)

        self.scaner_thread = False

    def wait_thread(self):
        self.stop_timers()

        if not self.scaner_thread or not self.scaner_thread.isRunning():
            self.start_thread()

        else:
            print(f"scaner wait prev thread finished, flag: {ScanerThreadManager.flag}")
            self.thread_wait_timer.start()

    def start_thread(self):
        self.stop_timers()

        if not MainUtils.smb_check():
            print("scaner no smb, 15 sec wait")
            self.smb_wait_timer.start()

        else:
            print("scaner start from shedule")
            self.scaner_thread = ScanerThread()
            self.scaner_thread.start()

            self.next_scan_timer.start()

    def stop_thread(self):
        print("run stop thread")
        ScanerThreadManager.flag = False
        self.stop_timers()

    def stop_timers(self):
        self.smb_wait_timer.stop()
        self.thread_wait_timer.stop()
        self.next_scan_timer.stop()


scaner_app = ScanerShedule()
