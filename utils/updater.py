import os
import shutil
import subprocess

from PyQt5.QtCore import QObject, pyqtSignal

from cfg import Dynamic, JsonData
from widgets._runnable import URunnable


class UpdaterMain(QObject):
    no_connection = pyqtSignal()
    finished_ = pyqtSignal()

    def __init__(self):
        super().__init__()

    def go(self):
        for update_file_path in JsonData.udpdate_file_paths_:

            if os.path.exists(update_file_path):

                zip_filename = os.path.basename(update_file_path)
                destination = os.path.join(Dynamic.down_folder, zip_filename)

                if os.path.exists(destination):
                    os.remove(destination)

                shutil.copy2(update_file_path, destination)
                # subprocess.run(["open", "-R", destination])
                subprocess.run(["open", destination])

                self.finished_.emit()
                return True
        
        self.no_connection.emit()
        return False


class WorkerSignals(QObject):
    no_connection = pyqtSignal()
    finished_ = pyqtSignal()


class Updater(URunnable):
    finished_ = pyqtSignal()
    no_connection = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.signals_ = WorkerSignals()
        self.task_ = None

    def task(self):
        self.task_ = UpdaterMain()
        self.task_.no_connection.connect(self.signals_.no_connection.emit)
        self.task_.finished_.connect(self.signals_.finished_.emit)
        self.task_.go()
