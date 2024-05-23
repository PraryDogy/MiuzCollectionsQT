import os
import shutil
import subprocess
import time

from PyQt5.QtCore import QThread, pyqtSignal, QObject

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
            print("no zip file")

        if not zip_file:
            self.no_connection.emit()
            return

        downloaded_zip = os.path.join(cnf.down_folder, filename_zip_file)

        if os.path.exists(downloaded_zip):
            os.remove(downloaded_zip)

        shutil.copy2(zip_file, downloaded_zip)

        while not os.path.exists(downloaded_zip):
            time.sleep(1)
        time.sleep(1)

        app_file = os.path.join(cnf.down_folder, filename_app_file)

        if os.path.exists(app_file):
            shutil.rmtree(app_file)

        apple_script = f"""
            tell application \"Archive Utility\"
                open POSIX file "{downloaded_zip}"
            end tell
            """

        subprocess.run(["osascript", "-e", apple_script])

        while not os.path.exists(app_file):
            time.sleep(1)
        time.sleep(1)

        if os.path.exists(downloaded_zip):
            os.remove(downloaded_zip)

        subprocess.run(["open", "-R", app_file])

        apple_script = f"""
            tell application \"Archive Utility\"
                quit
            end tell
            """

        subprocess.run(["osascript", "-e", apple_script])

        self.finished.emit()
        print(1)


class Updater(QThread):
    finished = pyqtSignal()
    no_connection = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.task = None

    def run(self):
        self.task = UpdaterMain()
        self.task.no_connection.connect(self.no_connection_cmd)
        self.task.finished.connect(self.finished_cmd)
        self.task.go()

    def no_connection_cmd(self):
        self.no_connection.emit()

    def finished_cmd(self):
        self.finished.emit()

