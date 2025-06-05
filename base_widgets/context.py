from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QCloseEvent, QContextMenuEvent
from PyQt5.QtWidgets import QMenu


class ContextCustom(QMenu):
    closed = pyqtSignal()

    def __init__(self, event: QContextMenuEvent):
        self.ev = event
        super().__init__()

    def show_menu(self):
        self.exec_(self.ev.globalPos())

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.closed.emit()
        return super().closeEvent(a0)

    def mouseReleaseEvent(self, a0):
        if a0.button() == Qt.MouseButton.RightButton:
            a0.ignore()
        else:
            super().mouseReleaseEvent(a0)