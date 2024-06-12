from PyQt5.QtCore import QObject, pyqtSignal


class UtilsSignals(QObject):
    scaner_start = pyqtSignal()
    scaner_stop = pyqtSignal()

    def __init__(self):
        super().__init__()


utils_signals_app = UtilsSignals()