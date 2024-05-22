import os
import shutil
import subprocess
import time

from PyQt5.QtCore import QThread, pyqtSignal

from cfg import cnf


class UpdaterMain:
    def __init__(self):
        volumes = "Volumes"
        zip_file = "Studio/Photo/Art/Raw/2024/soft/MiuzCollections.zip"

        filename_zip_file = os.path.basename(zip_file)
        filename_app_file = os.path.splitext(filename_zip_file)[0] + ".app"

        drives = os.listdir(os.path.join(os.sep, volumes))
        drives = [
            os.path.join(os.sep, volumes, drive)
            for drive in drives
            ]
        
        try:
            zip_file = [
                os.path.join(drive, zip_file)
                for drive in drives
                if os.path.exists(os.path.join(drive, zip_file))
                ][0]

        except IndexError:
            print("no zip file")

        down_folder = cnf.down_folder
        downloaded_zip = os.path.join(down_folder, filename_zip_file)

        if os.path.exists(downloaded_zip):
            os.remove(downloaded_zip)

        shutil.copy2(zip_file, downloaded_zip)

        app_file = os.path.join(down_folder, filename_app_file)

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

        if os.path.exists(downloaded_zip):
            os.remove(downloaded_zip)

        subprocess.run(["open", "-R", app_file])

        apple_script = f"""
            tell application \"Archive Utility\"
                quit
            end tell
            """

        subprocess.run(["osascript", "-e", apple_script])


class Updater(QThread):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        UpdaterMain()
        self.finished.emit()



