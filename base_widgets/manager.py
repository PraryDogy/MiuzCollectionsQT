from PyQt5.QtCore import QObject

class Manager:
    wins = []
    threads = []

    @staticmethod
    def finish_thread(task: QObject):
        Manager.threads.remove(task)
        task.deleteLater()