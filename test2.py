from cfg import Static
import shutil


zp = shutil.make_archive(Static.HASH_DIR, "zip", Static.APP_SUPPORT_DIR)
print(zp)