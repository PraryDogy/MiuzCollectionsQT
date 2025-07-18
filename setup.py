# -*- coding: utf-8 -*-

"""
    python setup.py py2app
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime

from setuptools import setup

from cfg import Static

# ****************** DON'T CHANGE IT ******************


def remove_trash():

    trash = ("build", ".eggs", "dist")

    for i in trash:
        try:
            shutil.rmtree(i)
        except Exception as e:
            continue


def move_app_to_desktop(appname: str):

    desktop = os.path.expanduser("~/Desktop")

    dest = os.path.join(desktop, f"{appname}.app")
    src = os.path.join("dist", f"{appname}.app")

    try:
        if os.path.exists(dest):
            shutil.rmtree(dest)
    except Exception as e:
        print(e)

    try:
        shutil.move(src, dest)
    except Exception as e:
        print(e)

    try:
        subprocess.Popen(["open", "-R", dest])
    except Exception as e:
        print(e)


def include_files(folder_name: str) -> list[str, list]:
    return (
        folder_name,
        [os.path.join(folder_name, i) for i in os.listdir(folder_name)]
        )





# ****************** YOUR DATA ******************

AUTHOR = "Evgeny Loshkarev"  # "Evgeny Loshkarev"
SHORT_AUTHOR_NAME = "Evlosh" # "Evlosh"
COMPANY = "MIUZ Diamonds" # "MIUZ Diamonds"
APP_NAME = Static.APP_NAME
APP_VER = str(Static.APP_VER)
ICON_PATH = os.path.join(Static.INNER_IMAGES, "icon.icns")
MAIN_FILES = ["start.py"] # SINGLE OR MULTIPLE PYTHON FILES


DATA_FILES = [
    include_files("images"),
    include_files("scripts")
    ]





# ****************** DON'T CHANGE IT ******************

YEAR = datetime.now().year # CURRENT YEAR
BUNDLE_ID = f"com.{SHORT_AUTHOR_NAME}.{APP_NAME}" # DON'T CHANGE IT
PY2APP = "py2app" # DON'T CHANGE IT

OPTIONS = {
    "iconfile": ICON_PATH,
    "excludes": ["setuptools"],
    'includes': ['numpy', 'cv2'],
    "packages": ['numpy', 'cv2'],
    "plist": {
        "CFBundleName": APP_NAME,
        "CFBundleShortVersionString": APP_VER,
        "CFBundleVersion": APP_VER,
        "CFBundleIdentifier": BUNDLE_ID,
        "NSHumanReadableCopyright": (
            f"Created by {AUTHOR}"
            f"\nCopyright © {YEAR} {COMPANY}."
            f"\nAll rights reserved.")
            }
            }

print("Нажми 1 чтобы создать приложение с кешем из ApplicationSupport")

if input() == "1":
    print("Создаю приложение с кешем ApplicationSupport")

    src = Static.APP_SUPPORT_HASHDIR
    root = os.path.basename(Static.APP_SUPPORT_HASHDIR)
    app_sup = Static.APP_SUPPORT_DIR
    new_hashdir = shutil.make_archive(src, "zip", app_sup, root)

    DATA_FILES.append(
        ('_preload', [new_hashdir, Static.APP_SUPPORT_DB])
    )

else:
    print("Создаю приложение с пустым кешем")
    new_hashdir = None
    DATA_FILES.append(include_files("_preload"))

sys.argv.append(PY2APP)

try:
    remove_trash()

    setup(
        app=MAIN_FILES,
        name=APP_NAME,
        data_files=DATA_FILES,
        options={PY2APP: OPTIONS},
        setup_requires=[PY2APP],
        )

    move_app_to_desktop(APP_NAME)
    remove_trash()

except Exception as e:
    print(e)
    remove_trash()


if new_hashdir:
    os.remove(new_hashdir)
