import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLabel, QPushButton, QSpacerItem, QWidget

from cfg import Static
from system.lang import Lang

from ._base_widgets import SvgBtn, UHBoxLayout, UVBoxLayout, WinSystem


class WinFirstLoad(WinSystem):
    yes_pressed = pyqtSignal()
    no_pressed = pyqtSignal()

    def __init__(self, question: str):
        super().__init__()
        self.question = question

        self.central_layout.setContentsMargins(10, 10, 10, 10)
        self.central_layout.setSpacing(10)
        self.init_ui()
        self.adjustSize()

    def init_ui(self):
        v_wid = QWidget()
        self.central_layout.addWidget(v_wid)
        self.central_layout.setContentsMargins(10, 5, 10, 5)
        v_lay = UVBoxLayout()
        v_wid.setLayout(v_lay)

        lbl_descr = QLabel(self.question)
        v_lay.addWidget(lbl_descr)

        btn_wid = QWidget()
        v_lay.addWidget(btn_wid)
        btn_lay = UHBoxLayout()
        btn_lay.setSpacing(10)
        btn_wid.setLayout(btn_lay)

        btn_lay.addStretch()

        btn_yes = QPushButton("Да")
        btn_yes.clicked.connect(self.yes_cmd)
        btn_yes.setFixedWidth(100)
        btn_lay.addWidget(btn_yes)

        btn_no = QPushButton("Нет")
        btn_no.clicked.connect(self.no_cmd)
        btn_no.setFixedWidth(100)
        btn_lay.addWidget(btn_no)

        btn_lay.addStretch()

    def yes_cmd(self):
        self.yes_pressed.emit()
        self.deleteLater()

    def no_cmd(self):
        self.no_pressed.emit()
        self.deleteLater()

    def closeEvent(self, a0):
        a0.ignore()
