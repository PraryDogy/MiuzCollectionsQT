from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QMouseEvent, QContextMenuEvent
from PyQt5.QtWidgets import QMenu

from styles import Themes


class ContextMenuBase(QMenu):
    closed = pyqtSignal()

    def __init__(self, event: QContextMenuEvent):
        self.ev = event
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setMinimumWidth(200)
        self.setStyleSheet(Themes.current)
    
    def show_menu(self):
        self.exec_(self.ev.globalPos())

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.closed.emit()
        return super().closeEvent(a0)


class ContextSubMenuBase(QMenu):
    def __init__(self, parent: QMenu, title: str):
        super().__init__(parent=parent, title=title)
        self.setMinimumWidth(150)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        self.raise_()
        return super().mousePressEvent(a0)
