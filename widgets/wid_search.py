from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QLineEdit

from cfg import Dynamic, Cfg
from system.lang import Lng

from ._base_widgets import ULineEdit


class ClearBtn(QSvgWidget):
    clicked_ = pyqtSignal()
    svg_clear = "./images/clear.svg"
    svg_size = 14

    def __init__(self, parent: QLineEdit):
        super().__init__(parent=parent)
        self.setFixedSize(self.svg_size, self.svg_size)
        self.load(self.svg_clear)

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

    def __init__(self):
        super().__init__()
        self.setFixedWidth(150)

        self.textChanged.connect(self.create_search)
        self.setPlaceholderText(Lng.search[Cfg.lng])

        self.clear_btn = ClearBtn(parent=self)
        self.clear_btn.clicked_.connect(self.clear_search)
        self.clear_btn.disable()
        self.clear_btn.move(
            self.width() - ClearBtn.svg_size - 8,
            (ClearBtn.svg_size * 2) // 4
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
        Dynamic.loaded_thumbs = 0
        self.reload_thumbnails.emit()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.delayed_search()
        if a0.key() == Qt.Key.Key_Escape:
            self.clearFocus()
        return super().keyPressEvent(a0)
