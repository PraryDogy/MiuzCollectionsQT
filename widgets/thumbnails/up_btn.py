from PyQt5.QtWidgets import QWidget

from base_widgets import SvgShadowed, SvgBtn
from signals import gui_signals_app


class UpBtn(SvgBtn):
    def __init__(self, parent: QWidget):
        super().__init__(
            icon_name="up.svg",
            size=45,
            parent=parent,
            )

    def mouseReleaseEvent(self, event):
        gui_signals_app.scroll_top.emit()