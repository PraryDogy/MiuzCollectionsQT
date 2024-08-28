import os
import shutil
import subprocess
from .main_utils import MainUtils

from PyQt5.QtCore import QObject, pyqtSignal

from .my_thread import MyThread
from cfg import cnf


class UpdaterMain(QObject):
    no_connection = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()

    def go(self):
        for update_file_path in cnf.udpdate_file_paths:

            if os.path.exists(update_file_path):

                zip_filename = os.path.basename(update_file_path)
                destination = os.path.join(cnf.down_folder, zip_filename)

                if os.path.exists(destination):
                    os.remove(destination)

                shutil.copy2(update_file_path, destination)
                subprocess.run(["open", "-R", destination])

                self.finished.emit()
                return True
        
        self.no_connection.emit()
        return False


class Updater(MyThread):
    finished = pyqtSignal()
    no_connection = pyqtSignal()

    def __init__(self):
        super().__init__(parent=None)
        self.task = None

    def run(self):
        self.task = UpdaterMain()
        self.task.no_connection.connect(self.no_connection_cmd)
        self.task.finished.connect(self.finished_cmd)
        self.task.go()
        self.remove_threads()

    def no_connection_cmd(self):
        self.no_connection.emit()
        self.remove_threads()

    def finished_cmd(self):
        self.finished.emit()
        self.remove_threads()

