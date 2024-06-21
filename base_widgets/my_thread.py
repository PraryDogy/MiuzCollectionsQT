from PyQt5.QtCore import QThread, QObject
from .manager import Manager


class MyThread(QThread):
    def __init__(self, parent: QObject):
        super().__init__(parent=parent)
        Manager.threads.append(self)

    def remove_threads(self):
        """Remove dead threads"""
        try:
            for i in Manager.threads:
                i: QThread
                if not i.isRunning():
                    Manager.threads.remove(i)
        except Exception as e:
            print("Base Widgets > my_thread.py > remove_thread", e)
