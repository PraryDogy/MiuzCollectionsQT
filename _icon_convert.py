import os

import icnsutil


def convert():
    if os.path.exists("icon/icon.png"):
        print("convert to png")
        img = icnsutil.IcnsFile()
        img.add_media(file="icon/icon.png")
        img.write("icon/icon.icns")
        os.remove("icon/icon.png")



# convert()