import shutil
import os
import subprocess

class SetupExt:
    def __init__(self, appname: str):
        desktop = os.path.expanduser("~/Desktop")

        dest = os.path.join(
            desktop,
            f"{appname}.app"
            )

        src = os.path.join(
            "dist",
            f"{appname}.app"
            )

        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.move(src, dest)

        for i in ("build", ".eggs", "dist"):
            if os.path.exists(i):
                shutil.rmtree(i)

        subprocess.Popen(["open", "-R", dest])


if __name__ == "__main__":
    shutil.rmtree("build")
    shutil.rmtree(".eggs")
    shutil.rmtree("dist")