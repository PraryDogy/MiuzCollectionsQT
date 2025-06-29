import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLabel, QPushButton, QSpacerItem, QWidget

from cfg import Static
from system.lang import Lang

from ._base_widgets import SvgBtn, UHBoxLayout, UVBoxLayout, WinSystem


class WinFirstLoad(WinSystem):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Первый запуск")

        self.central_layout.setContentsMargins(10, 10, 10, 10)
        self.central_layout.setSpacing(10)
        self.init_ui()
        self.adjustSize()

    def init_ui(self):
        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)
        v_lay = UVBoxLayout()
        h_wid.setLayout(v_lay)



    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.deleteLater()