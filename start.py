import os
import sys
import traceback

from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton


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
    ...
    plugin_path = "lib/python3.11/PyQt5/Qt5/plugins"
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path
    sys.excepthook = catch_err
    print()
    print(f"plugin path enabled")
    print()


from database import Dbase
Dbase.create_engine()

from app import app
app.exec_()

# source deacivate
# import app происходит только после активации os.environ plugin_path