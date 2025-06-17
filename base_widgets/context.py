from PyQt5.QtCore import Qt
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QMenu


class ContextCustom(QMenu):

    def __init__(self, event: QContextMenuEvent):
        self.ev = event
        super().__init__()

    def show_menu(self):
        self.exec_(self.ev.globalPos())

    def mouseReleaseEvent(self, a0):
        if a0.button() == Qt.MouseButton.RightButton:
            a0.ignore()
        else:
            super().mouseReleaseEvent(a0)