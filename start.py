import logging
import os
import sys
import traceback

from PyQt5.QtWidgets import QMessageBox

from cfg import cnf


def log_unhandled_exception(exc_type, exc_value, exc_traceback):
    error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    show_error_dialog(error_message)

def show_error_dialog(error_message):
    error_dialog = QMessageBox()
    error_dialog.setIcon(QMessageBox.Critical)
    error_dialog.setWindowTitle("Error / Ошидка")

    tt = [
        "Отправьте ошибку / Send error",
        "email: loshkarev@miuz.ru",
        "tg: evlosh"]
    
    tt = "\n".join(tt)
    
    error_dialog.setText(tt)
    error_dialog.setDetailedText(error_message)
    error_dialog.exec_()


if os.path.exists("lib"): 
    #lib folder appears when we pack this project to .app with py2app

    py_ver = sys.version_info
    py_ver = f"{py_ver.major}.{py_ver.minor}"

    plugin_path = os.path.join(
        "lib",
        f"python{py_ver}",
        "PyQt5",
        "Qt5",
        "plugins",
        )

    log = os.path.join(
        cnf.app_support_app_dir,
        "log.txt"
        )

    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path
    logging.basicConfig(filename=log, level=logging.ERROR)
    sys.excepthook = log_unhandled_exception

    print("logging enabled")
    print(f"plugin path enabled {plugin_path}")

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

