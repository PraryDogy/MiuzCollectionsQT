from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QMenu

from styles import default_theme


class ContextMenuBase(QMenu):
    def __init__(self, event):
        self.ev = event
        super().__init__()

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setMinimumWidth(200)
        self.setStyleSheet(default_theme)
    
    def show_menu(self):
        self.exec_(self.ev.globalPos())


class ContextSubMenuBase(QMenu):
    def __init__(self, parent: QMenu, title):
        super().__init__(parent)
        self.setTitle(title)
        self.setMinimumWidth(150)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        self.raise_()
        return super().mousePressEvent(a0)