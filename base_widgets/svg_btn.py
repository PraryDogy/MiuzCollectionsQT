from PyQt5.QtSvg import QSvgWidget
import os
from PyQt5.QtWidgets import QWidget
from .layouts import LayoutH


class SvgBtn(QWidget):
    def __init__(self, icon_name: str, size: int):
        QWidget.__init__(self)

        h_layout = LayoutH()
        self.setLayout(h_layout)

        self.svg_btn = QSvgWidget(os.path.join("images", icon_name))
        self.svg_btn.setFixedSize(size, size)
        h_layout.addWidget(self.svg_btn)

    def set_icon(self, icon_name):
        self.svg_btn.load(os.path.join("images", icon_name))
