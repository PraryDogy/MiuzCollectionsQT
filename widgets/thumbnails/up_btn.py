from PyQt5.QtWidgets import QWidget

from base_widgets import SvgShadowed
from signals import gui_signals_app


class UpBtn(SvgShadowed):
    def __init__(self, parent: QWidget):
        super().__init__(
            icon_name="up.svg",
            size=60,
            parent=parent,
            shadow_depth=240
            )

    def mouseReleaseEvent(self, event):
        gui_signals_app.scroll_top.emit()