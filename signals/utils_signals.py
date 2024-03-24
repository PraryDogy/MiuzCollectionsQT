from PyQt5.QtCore import QObject, pyqtSignal


class UtilsSignals(QObject):
    watcher_start = pyqtSignal()
    watcher_stop = pyqtSignal()
    watcher_timer = pyqtSignal()

    scaner_start = pyqtSignal()
    scaner_stop = pyqtSignal()
    scaner_err = pyqtSignal()

    def __init__(self):
        super().__init__()


utils_signals_app = UtilsSignals()