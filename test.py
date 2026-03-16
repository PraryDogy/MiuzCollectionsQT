import os
import shutil

from cfg import Static

src = Static.external_files_dir
root = os.path.basename(Static.external_files_dir)
app_sup = os.path.dirname(Static.external_files_dir)
new_hashdir = shutil.make_archive("./_preload/test", "zip", app_sup, root)