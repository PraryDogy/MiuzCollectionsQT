import os
import subprocess

APP_NAME = "MiuzCollections"
ERROR_MSG = "HELLO"

FILE_: str = os.path.join(
    os.path.expanduser("~"),
    "Library",
    "Application Support",
    APP_NAME + "QT",
    "error.html"
    )
with open(FILE_, "w")as f:
    f.write(ERROR_MSG)


with open(FILE_, "w") as f:
    f.write(ERROR_MSG)

subprocess.run(["open", FILE_])