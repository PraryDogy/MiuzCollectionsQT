import os

import icnsutil


def convert():
    if os.path.exists("icon/icon.png"):
        img = icnsutil.IcnsFile()
        img.add_media(file="icon.png")
        img.write("icon/icon.icns")
        os.remove("icon/icon.png")