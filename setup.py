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
from cfg import cnf

def remove_trash():
    trash = ("build", ".eggs", "dist")
    for i in trash:
        try:
            shutil.rmtree(i)
        except Exception as e:
            print(e)
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


YEAR = datetime.now().year # CURRENT YEAR
AUTHOR = "Evgeny Loshkarev"  # "Evgeny Loshkarev"
SHORT_AUTHOR_NAME = "Evlosh" # "Evlosh"
COMPANY = "MIUZ Diamonds" # "MIUZ Diamonds" or ""
APP_NAME = cnf.app_name
APP_VER = cnf.app_ver
ICON_PATH = "icon/icon.icns" # "icon/icon.icns" or "icon.icns"
MAIN_FILES = ["start.py"] # SINGLE OR MULTIPLE PYTHON FILES

BUNDLE_ID = f"com.{SHORT_AUTHOR_NAME}.{APP_NAME}" # DON'T CHANGE IT
PY_2APP = "py2app" # DON'T CHANGE IT


images = [
    os.path.join("images", i)
    for i in os.listdir("images")
    if i.endswith((".svg", ".jpg"))
    ]

applescripts = [
    os.path.join("applescripts", i)
    for i in os.listdir("applescripts")
    if i.endswith((".scpt"))
    ]

styles = [
    os.path.join("styles", i)
    for i in os.listdir("styles")
    if i.endswith((".css"))
]

icons = [
    os.path.join("icon", i)
    for i in os.listdir("icon")
    ]

DATA_FILES = [
    "db.db",
    "lang/lang.json",
    ("images", images),
    ("applescripts", applescripts),
    ("styles", styles),
    ("icon", icons)
    ]


# DON'T CHANGE IT

OPTIONS = {"iconfile": ICON_PATH,
           "plist": {"CFBundleName": APP_NAME,
                     "CFBundleShortVersionString": APP_VER,
                     "CFBundleVersion": APP_VER,
                     "CFBundleIdentifier": BUNDLE_ID,
                     "NSHumanReadableCopyright": (
                         f"Created by {AUTHOR}"
                         f"\nCopyright © {YEAR} {COMPANY}."
                         f"\nAll rights reserved.")}}


if __name__ == "__main__":

    print()
    print("Copy db file from App Support?")
    print("Type \"1\" to confirm")
    print()
    res = input()
    if res == "1":
        shutil.copyfile(src=cnf.db_file, dst="db.db")

    sys.argv.append(PY_2APP)

    try:
        remove_trash()

        setup(
            app=MAIN_FILES,
            name=APP_NAME,
            data_files=DATA_FILES,
            options={PY_2APP: OPTIONS},
            setup_requires=[PY_2APP],
            )

        move_app_to_desktop(APP_NAME)
        remove_trash()

    except Exception as e:
        print(e)
        remove_trash()
