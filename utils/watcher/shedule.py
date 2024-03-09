from PyQt5.QtCore import QObject, QTimer

from .. import utils_signals_app
from ..main_utils import MainUtils
from .thread import WatcherThread


class WatcherShedule(QObject):
    def __init__(self):
        super().__init__()

        ms = 15000
        self.timer = QTimer(self)
        self.timer.setInterval(ms)
        self.timer.timeout.connect(self.start_sheduled)

        utils_signals_app.watcher_start.connect(self.start_sheduled)
        utils_signals_app.watcher_stop.connect(self.stop_watcher_thread)

        self.watcher_thread = None

    def start_sheduled(self):

        if MainUtils.smb_check():
            self.watcher_thread = WatcherThread()
            self.watcher_thread.start()

        else:
            self.timer.start()

    def stop_watcher_thread(self):
        if self.watcher_thread:
            self.watcher_thread.clean_engine()
            self.watcher_thread.stop_watcher()


watcher_app = WatcherShedule()