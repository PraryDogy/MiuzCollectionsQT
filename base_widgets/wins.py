from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import QFrame, QMainWindow, QWidget

from utils.utils import Utils

from .layouts import LayoutVer


class Manager:
    wins: list[QMainWindow] = []


class WinFrameless(QMainWindow):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)

        central_widget = QWidget()
        central_widget.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(central_widget)

        self.central_layout_v = LayoutVer()
        central_widget.setLayout(self.central_layout_v)

        Manager.wins.append(self)

    def center_relative_parent(self, parent: QMainWindow):

        if not isinstance(parent, QMainWindow):
            raise TypeError

        try:
            geo = self.geometry()
            geo.moveCenter(parent.geometry().center())
            self.setGeometry(geo)
        except (RuntimeError, Exception) as e:
            Utils.print_err(error=e)

    def disable_min(self):
        print("флаги не включены")
        return
        fl = Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint
        fl = fl  | Qt.WindowType.WindowCloseButtonHint
        self.setWindowFlags(fl)

    def enable_min(self):
        self.setWindowFlag(Qt.WindowType.Widget)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        try:
            Manager.wins.remove(self)
            self.deleteLater()
        except Exception as e:
            pass
        return super().closeEvent(a0)


class WinChild(WinFrameless):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.disable_min()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # у этого виджета закруглены только нижние углы
        self.content_wid = QFrame()
        self.central_layout_v.addWidget(self.content_wid)

        self.content_lay_v = LayoutVer()
        self.content_lay_v.setContentsMargins(10, 5, 10, 5)
        self.content_wid.setLayout(self.content_lay_v)
