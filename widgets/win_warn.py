import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLabel, QPushButton, QSpacerItem, QWidget

from cfg import Static
from system.lang import Lang

from ._base_widgets import SvgBtn, UHBoxLayout, UVBoxLayout, WinSystem

WARNING_SVG = os.path.join(Static.images_dir, "warning.svg")


class WinWarn(WinSystem):
    def __init__(self, title: str, text: str):
        super().__init__()
        self.setWindowTitle(title)
        self.my_text = text

        self.central_layout.setContentsMargins(10, 10, 10, 10)
        self.central_layout.setSpacing(10)
        self.init_ui()
        self.adjustSize()

    def init_ui(self):
        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)
        h_layout = UHBoxLayout()
        h_wid.setLayout(h_layout)

        warning = SvgBtn(WARNING_SVG, 40)
        h_layout.addWidget(warning)

        h_layout.addSpacerItem(QSpacerItem(15, 0))

        v_wid = QWidget()
        h_layout.addWidget(v_wid)
        v_lay = UVBoxLayout()
        v_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        v_wid.setLayout(v_lay)

        descr = QLabel(self.my_text)
        v_lay.addWidget(descr)

        ok_btn = QPushButton(text=Lang.ok)
        ok_btn.setFixedWidth(90)
        ok_btn.clicked.connect(self.close)
        self.central_layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.deleteLater()