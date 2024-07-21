import os
import sys
import traceback

from PyQt5.QtWidgets import QMessageBox

from app import app


def log_unhandled_exception(exc_type, exc_value, exc_traceback):
    error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
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
    plugin_path = os.path.join("lib", f"python{py_ver}", "PyQt5", "Qt5", "plugins")
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path
    print(f"plugin path enabled {plugin_path}")

    sys.excepthook = log_unhandled_exception

sys.excepthook = log_unhandled_exception
app.exec_()
