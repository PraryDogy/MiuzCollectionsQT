import os

from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QFrame, QWidget

from base_widgets import LayoutV, SvgBtn
from signals import signals_app
from styles import Names, Themes


class UpBtn(QFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self.setObjectName(Names.up_btn)
        self.setStyleSheet(Themes.current)

        v_layout = LayoutV()
        self.setLayout(v_layout)

        self.svg = SvgBtn(os.path.join("images", "up_new.svg"), 44)
        v_layout.addWidget(self.svg)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        signals_app.scroll_top.emit()
        return super().mouseReleaseEvent(a0)
