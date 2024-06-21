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
        volumes = "Volumes"

        filename_zip_file = os.path.basename(cnf.updater_path)
        filename_app_file = os.path.splitext(filename_zip_file)[0] + ".app"

        drives = os.listdir(os.path.join(os.sep, volumes))
        drives = [
            os.path.join(os.sep, volumes, drive)
            for drive in drives
            ]
        
        try:
            zip_file = [
                os.path.join(drive, cnf.updater_path)
                for drive in drives
                if os.path.exists(os.path.join(drive, cnf.updater_path))
                ][0]

        except IndexError:
            zip_file = None
            MainUtils.print_err(parent=self, error=e)

        if not zip_file:
            self.no_connection.emit()
            return

        downloaded_zip = os.path.join(cnf.down_folder, filename_zip_file)

        if os.path.exists(downloaded_zip):
            os.remove(downloaded_zip)

        shutil.copy2(zip_file, downloaded_zip)
        subprocess.run(["open", "-R", downloaded_zip])

        self.finished.emit()


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

