import logging
import os
import sys

from cfg import cnf


def log_unhandled_exception(exc_type, exc_value, exc_traceback):
    logging.error(
        "Необработанное исключение",
        exc_info=(exc_type, exc_value, exc_traceback)
        )


if os.path.exists("lib"): 
    #lib folder appears when we pack this project to .app with py2app

    py_ver = sys.version_info
    py_ver = f"{py_ver.major}.{py_ver.minor}"

    plugin_path = os.path.join(
        "lib",
        f"python{py_ver}",
        "PyQt5",
        "plugins"
        )

    log = os.path.join(
        cnf.app_support_app_dir,
        "log.txt"
        )

    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path
    logging.basicConfig(filename=log, level=logging.ERROR)
    sys.excepthook = log_unhandled_exception

    print("logging enabled")
    print("plugin path enabled")

try:
    from app import app
    app.exec_()

except Exception as e:
    print(e)
    print("try set to default settings")

    import os

    from cfg import cnf

    os.remove(cnf.json_file)
    cnf.set_default()
    cnf.check_app_dirs()

    from app import app
    app.exec_()

