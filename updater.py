import os
import shutil
import zipfile
from cfg import cnf
 
class Updater:
    def __init__(self):
        self.path = self.get_path()
        self.download_zip()

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


Updater()