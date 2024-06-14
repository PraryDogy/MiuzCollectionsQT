# -*- coding: utf-8 -*-

"""
    python setup.py py2app
"""

import os
import shutil
import sys
import traceback
from datetime import datetime

from setuptools import setup

from cfg import cnf
from setup_ext import SetupExt

current_year = datetime.now().year

APP = ["start.py"]

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

logos = [
    os.path.join("logo", i)
    for i in os.listdir("logo")
    ]


DATA_FILES = [
    "db.db",
    "lang/lang.json",
    ("images", images),
    ("applescripts", applescripts),
    ("styles", styles),
    ("logo", logos)
    ]

OPTIONS = {"iconfile": "logo/icon.icns",
           "plist": {"CFBundleName": cnf.app_name,
                     "CFBundleShortVersionString": cnf.app_ver,
                     "CFBundleVersion": cnf.app_ver,
                     "CFBundleIdentifier": f"com.evlosh.{cnf.app_name}",
                     "NSHumanReadableCopyright": (
                         f"Created by Evgeny Loshkarev"
                         f"\nCopyright © {current_year} MIUZ Diamonds."
                         f"\nAll rights reserved.")}}


if __name__ == "__main__":

    print()
    print("Copy db file from App Support?")
    print("Type \"1\" to confirm")
    print()
    res = input()
    if res == "1":
        shutil.copyfile(src=cnf.db_file, dst="db.db")

    sys.argv.append("py2app")

    try:
        setup(
            app=APP,
            name=cnf.app_name,
            data_files=DATA_FILES,
            options={"py2app": OPTIONS},
            setup_requires=["py2app"],
            )
        SetupExt(appname=cnf.app_name)

    except Exception:
        print(traceback.format_exc())

        try:
            shutil.rmtree("build")
            shutil.rmtree(".eggs")
            shutil.rmtree("dist")
        except FileNotFoundError:
            pass
