from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QCloseEvent, QMouseEvent
from PyQt5.QtWidgets import QMenu

from styles import Themes


class ContextMenuBase(QMenu):
    closed = pyqtSignal()

    def __init__(self, event):
        self.ev = event
        super().__init__()

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setMinimumWidth(200)
        self.setStyleSheet(Themes.current)
    
    def show_menu(self):
        self.exec_(self.ev.globalPos())

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.closed.emit()
        return super().closeEvent(a0)


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
