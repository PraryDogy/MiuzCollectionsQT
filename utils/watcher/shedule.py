from PyQt5.QtCore import QObject, QTimer

from .. import utils_signals_app
from ..main_utils import MainUtils
from .thread import WatcherThread


class WatcherShedule(QObject):
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

        utils_signals_app.watcher_start.connect(self.wait_thread)
        utils_signals_app.watcher_stop.connect(self.stop_thread)

        self.watcher_thread = False

    def wait_thread(self):
        self.stop_timers()

        if not self.watcher_thread or not self.watcher_thread.isRunning():
            self.start_thread()
        
        else:
            print("watcher wait prev thread stop")
            self.thread_wait_timer.start()

    def start_thread(self):
        if MainUtils.smb_check():
            print("watcher started from shedule")

            self.stop_timers()
            self.watcher_thread = WatcherThread()
            self.watcher_thread.start()

        else:
            print("watcher no smb, 15 sec wait")
            self.smb_wait_timer.start()

    def stop_thread(self):
        if self.watcher_thread:
            self.stop_timers()
            self.watcher_thread.clean_engine()
            self.watcher_thread.stop_watcher()

    def stop_timers(self):
        self.smb_wait_timer.stop()
        self.thread_wait_timer.stop()


watcher_app = WatcherShedule()