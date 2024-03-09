from PyQt5.QtCore import QObject, QTimer

from signals import utils_signals_app
from ..main_utils import MainUtils
from .thread import ScanerThread


class ScanerShedule(QObject):
    def __init__(self):
        super().__init__()
        smb_check_mins = 15000
        # scan_again_mins = 15 * 60 * 1000
        # big_mins = 10000

        self.small_wait_timer = QTimer(self)
        self.small_wait_timer.setInterval(smb_check_mins)
        self.small_wait_timer.timeout.connect(self.start_sheduled)

        # self.big_wait_timer = QTimer(self)
        # self.big_wait_timer.setInterval(scan_again_mins)
        # self.big_wait_timer.timeout.connect(self.start_sheduled)

        utils_signals_app.scaner_start.connect(self.start_sheduled)
        utils_signals_app.scaner_stop.connect(self.stop_scaner_thread)
        utils_signals_app.scan_finished_with_err.connect(self.start_sheduled)


    def start_sheduled(self):
        self.scaner_thread = ScanerThread()

        self.small_wait_timer.stop()
        # self.big_wait_timer.stop()

        if not MainUtils.smb_check():
            print("scaner no smb, 15 sec wait")
            self.small_wait_timer.start()

        else:
            print("scaner start from shedule")
            self.scaner_thread.start()
            # self.big_wait_timer.start()

    def stop_scaner_thread(self):
        self.scaner_thread.quit()
        utils_signals_app.scaner_stoped.emit()


scaner_app = ScanerShedule()