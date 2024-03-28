from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QSpacerItem, QMessageBox

from base_widgets import Btn, WinStandartBase
from cfg import cnf
from signals import gui_signals_app


class WinErr(QMessageBox):
    def __init__(self, title: str, descr: str):
        super().__init__()
        self.setIcon(QMessageBox.Icon.Warning)
        self.setWindowTitle(title)
        self.setText(descr)
        self.exec()