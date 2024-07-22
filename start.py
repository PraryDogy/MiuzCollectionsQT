import os
import sys
import traceback

from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton

from app import app


def catch_err(exc_type, exc_value, exc_traceback):
    error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    error_dialog(error_message)


def error_dialog(error_message):
    error_dialog = QMessageBox()
    error_dialog.setIcon(QMessageBox.Critical)
    error_dialog.setWindowTitle("Error / Ошибка")

    tt = "\n".join(["Отправьте ошибку / Send error", "email: loshkarev@miuz.ru", "tg: evlosh"])
    error_dialog.setText(tt)
    error_dialog.setDetailedText(error_message)

    exit_button = QPushButton("Выход")
    exit_button.clicked.connect(QApplication.quit)
    error_dialog.addButton(exit_button, QMessageBox.ActionRole)

    error_dialog.exec_()


if os.path.exists("lib"): 
    #lib folder appears when we pack this project to .app with py2app

    py_ver = sys.version_info
    py_ver = f"{py_ver.major}.{py_ver.minor}"
    plugin_path = os.path.join("lib", f"python{py_ver}", "PyQt5", "Qt5", "plugins")
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path
    print(f"plugin path enabled {plugin_path}")

    sys.excepthook = catch_err


app.exec_()


# source deacivate