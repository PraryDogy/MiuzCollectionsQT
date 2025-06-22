from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QMainWindow, QWidget

from utils.main import MainUtils

from .layouts import LayoutVer


class Manager:
    wins: list[QMainWindow] = []


class WinFrameless(QMainWindow):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)

        central_widget = QWidget()
        central_widget.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(central_widget)

        self.central_layout = LayoutVer()
        central_widget.setLayout(self.central_layout)

        Manager.wins.append(self)

    def center_relative_parent(self, parent: QMainWindow):

        if not isinstance(parent, QMainWindow):
            raise TypeError

        try:
            geo = self.geometry()
            geo.moveCenter(parent.geometry().center())
            self.setGeometry(geo)
        except (RuntimeError, Exception) as e:
            MainUtils.print_error()

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        try:
            Manager.wins.remove(self)
        except Exception as e:
            pass
        return super().closeEvent(a0)
    
    def deleteLater(self):
        try:
            Manager.wins.remove(self)
        except Exception as e:
            pass
        return super().deleteLater()


class WinSystem(WinFrameless):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        fl = Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint
        fl = fl  | Qt.WindowType.WindowCloseButtonHint
        self.setWindowFlags(fl)

        self.central_layout.setContentsMargins(10, 5, 10, 5)


class WinChild(WinFrameless):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)