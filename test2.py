from cfg import Static
import shutil
import os

zp = shutil.make_archive(
    Static.HASH_DIR,
    "zip",
    Static.APP_SUPPORT_DIR,
    os.path.basename(Static.HASH_DIR)
    )