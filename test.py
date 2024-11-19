import os
import shutil
import subprocess
import zipapp

from cfg import APP_SUPPORT_DIR, HASH_DIR, PRELOAD_HASHDIR_ZIP

if os.path.exists(PRELOAD_HASHDIR_ZIP):
    print("копирую предустановленную HASH_DIR")
    dest = shutil.copy2(PRELOAD_HASHDIR_ZIP, APP_SUPPORT_DIR)
    # subprocess.run(["open", dest])
    shutil.unpack_archive(dest, APP_SUPPORT_DIR)