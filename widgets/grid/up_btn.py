import os

from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QFrame, QWidget

from base_widgets import LayoutVer, SvgBtn
from signals import SignalsApp
from utils.utils import Utils


class UpBtn(QFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self.setObjectName("up_btn")
        Utils.style(self)

        v_layout = LayoutVer()
        self.setLayout(v_layout)

        self.svg = SvgBtn(os.path.join("images", "up_new.svg"), 44)
        v_layout.addWidget(self.svg)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        SignalsApp.all_.grid_thumbnails_cmd.emit("to_top")
        return super().mouseReleaseEvent(a0)
