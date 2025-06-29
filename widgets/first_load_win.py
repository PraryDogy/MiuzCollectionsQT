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

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Первый запуск")

        self.central_layout.setContentsMargins(10, 10, 10, 10)
        self.central_layout.setSpacing(10)
        self.init_ui()
        self.adjustSize()

    def init_ui(self):
        v_wid = QWidget()
        self.central_layout.addWidget(v_wid)
        v_lay = UVBoxLayout()
        v_wid.setLayout(v_lay)

        t = "Вы из MiuzDiamonds/Panacea?\nНажмите да, и приложение установит настройки"
        lbl_descr = QLabel(t)
        v_lay.addWidget(lbl_descr)

        btn_wid = QWidget()
        v_lay.addWidget(btn_wid)
        btn_lay = UHBoxLayout()
        btn_wid.setLayout(btn_lay)

        btn_lay.addStretch()

        btn_yes = QPushButton("Да")
        btn_yes.clicked.connect(self.yes_pressed.emit)
        btn_yes.setFixedWidth(100)
        btn_lay.addWidget(btn_yes)

        btn_no = QPushButton("Нет")
        btn_no.clicked.connect(self.no_pressed.emit)
        btn_no.setFixedWidth(100)
        btn_lay.addWidget(btn_no)

        btn_lay.addStretch()


    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.deleteLater()