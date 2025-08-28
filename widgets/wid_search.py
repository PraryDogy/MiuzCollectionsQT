import os

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QLineEdit

from cfg import Dynamic, Static
from system.lang import Lang

from ._base_widgets import ULineEdit

CLEAR_SVG = os.path.join(Static.INNER_IMAGES, "clear.svg")
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

    def enterEvent(self, a0):
        self.setCursor(Qt.CursorShape.ArrowCursor)


class WidSearch(ULineEdit):
    reload_thumbnails = pyqtSignal()
    scroll_to_top = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(150)

        self.textChanged.connect(self.create_search)
        self.setPlaceholderText(Lang.search)

        self.clear_btn = ClearBtn(parent=self)
        self.clear_btn.clicked_.connect(self.clear_search)
        self.clear_btn.disable()
        self.clear_btn.move(
            self.width() - CLEAR_SIZE - 8,
            INPUT_H // 4
        )

    def create_search(self, new_text):
        if len(new_text) > 0:
            Dynamic.search_widget_text = new_text
            self.clear_btn.enable()
        else:
            Dynamic.search_widget_text = None
            self.clear_btn.disable()

    def delayed_search(self):
        self.reload_thumbnails.emit()

    def clear_search(self):
        self.clear()
        Dynamic.search_widget_text = None
        Dynamic.grid_buff_size = 0
        self.reload_thumbnails.emit()
        self.scroll_to_top.emit()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.delayed_search()
        if a0.key() == Qt.Key.Key_Escape:
            self.clearFocus()
        return super().keyPressEvent(a0)
