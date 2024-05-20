import os
import shutil
import subprocess
import zipfile

from cfg import cnf


class Updater:
    def __init__(self):
        self.path = self.get_path()
        unzipped_app = self.download_zip()
        self.run_udate(unzipped_app)

    def get_path(self):
        possible_paths = (
            "/Volumes/Shares-1/Studio/Photo/Art/Raw/2024/soft",
            "/Volumes/Shares/Studio/Photo/Art/Raw/2024/soft"
            )
        
        for i in possible_paths:
            if os.path.exists(i):
                return i
        return None
    
    def download_zip(self):
        filename = f"{cnf.app_name}.zip"
        src = os.path.join(self.path, filename)
        dest = os.path.join(cnf.app_support_app_dir, filename)
        shutil.copy2(src, dest)
        
        with zipfile.ZipFile(dest, 'r') as zip_ref:
            zip_ref.extractall(cnf.app_support_app_dir)

            return os.path.join(
                cnf.app_support_app_dir,
                cnf.app_name + ".app",
                )

    def run_udate(self, unzipped_app: str):
        exit_app = "applescripts/exit_app.scpt"
        run_app = "applescripts/run_app.scpt"
        
        command = ["osascript", exit_app, cnf.app_name]
        subprocess.run(command)

        ext = ".app"
        current_path: str = os.path.dirname(__file__)
        app_index = current_path.find(ext)

        dest = current_path[:app_index] + ext
        shutil.copy2(unzipped_app, dest)

        command = ["osascript", run_app, cnf.app_name]
        subprocess.run(command)


Updater()
