from PyQt5.QtCore import QObject, QThread


class Threads:
    list = []


class MyThread(QThread):
    def __init__(self, parent: QObject):
        super().__init__(parent=parent)
        Threads.list.append(self)

    def remove_threads(self):
        """Remove dead threads"""
        try:
            for i in Threads.list:
                i: QThread
                if not i.isRunning():
                    Threads.list.remove(i)
        except Exception as e:
            print("Base Widgets > my_thread.py > remove_thread", e)
