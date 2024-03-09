from PyQt5.QtCore import QObject, QTimer

from signals import utils_signals_app
from ..main_utils import MainUtils
from .thread import ScanerThread, Manager as ScanerThreadManager


class ScanerShedule(QObject):
    def __init__(self):
        super().__init__()
        smb_check_ms = 15000

        self.small_wait_timer = QTimer(self)
        self.small_wait_timer.setInterval(smb_check_ms)
        self.small_wait_timer.timeout.connect(self.start_sheduled)

    def start_sheduled(self):
        self.scaner_thread = ScanerThread()
        self.small_wait_timer.stop()

        if not MainUtils.smb_check():
            print("scaner no smb, 15 sec wait")
            self.small_wait_timer.start()

        else:
            print("scaner start from shedule")
            self.scaner_thread.start()

    def stop_scaner_thread(self):
        ScanerThreadManager.flag = False


scaner_app = ScanerShedule()
utils_signals_app.scaner_start.connect(scaner_app.start_sheduled)
utils_signals_app.scaner_stop.connect(scaner_app.stop_scaner_thread)