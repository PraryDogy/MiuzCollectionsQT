import os
from typing import Literal

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QLineEdit, QSpacerItem, QWidget

from base_widgets import LayoutHor
from base_widgets.input import ULineEdit
from cfg import Dynamic, Static
from lang import Lang
from signals import SignalsApp

CLEAR_SVG = os.path.join(Static.IMAGES, "clear.svg")
CLEAR_SIZE = 14
INPUT_H = 28


class ClearBtn(QSvgWidget):
    clicked_ = pyqtSignal()

    def __init__(self, parent: QLineEdit):
        super().__init__(parent=parent)
        self.setFixedSize(CLEAR_SIZE, CLEAR_SIZE)
        self.load(CLEAR_SVG)

    def disable(self):
        self.hide()
        self.setDisabled(True)

    def enable(self):
        self.show()
        self.setDisabled(False)

    def mouseReleaseEvent(self, ev):
        self.clicked_.emit()


class WidSearch(ULineEdit):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(150)

        self.textChanged.connect(self.create_search)
        self.setPlaceholderText(Lang.search)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.delayed_search)

        self.clear_btn = ClearBtn(parent=self)
        self.clear_btn.clicked_.connect(self.clear_search)
        self.clear_btn.disable()
        self.clear_btn.move(
            self.width() - CLEAR_SIZE - 8,
            INPUT_H // 4
        )

        SignalsApp.all_.wid_search_cmd.connect(self.wid_search_cmd)

    def wid_search_cmd(self, flag: Literal["focus"]):
        if flag == "focus":
            self.setFocus()
        else:
            raise Exception("widgets > wid search > wrong flag", flag)

    def create_search(self, new_text):
        if len(new_text) > 0:
            Dynamic.search_widget_text = new_text
            self.clear_btn.enable()
        else:
            Dynamic.search_widget_text = None
            self.clear_btn.disable()

        self.timer.stop()
        self.timer.start()

    def delayed_search(self):
        SignalsApp.all_.grid_thumbnails_cmd.emit("reload")

    def clear_search(self):
        self.clear()
        Dynamic.search_widget_text = None
        Dynamic.grid_offset = 0
        SignalsApp.all_.grid_thumbnails_cmd.emit("reload")
        SignalsApp.all_.grid_thumbnails_cmd.emit("to_top")

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.clearFocus()
        return super().keyPressEvent(a0)
