import os

from PyQt5.QtCore import QEvent, QObject, QPoint, Qt, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QKeyEvent, QMouseEvent, QResizeEvent
from PyQt5.QtWidgets import (QFrame, QLabel, QMainWindow, QSizeGrip,
                             QSpacerItem, QWidget)

from cfg import JsonData
from styles import Names, Themes
from utils.utils import Utils

from .layouts import LayoutHor, LayoutVer
from .svg_btn import SvgBtn

# IMAGES_FOLDER = "images"

# CLOSE_FOCUS = "close-2.svg"
# CLOSE_NONFOCUS = "close-1.svg"

# MIN_FOCUS = "min-2.svg"
# MIN_NONFOCUS = "min-1.svg"

# MAX_FOCUS = "max-2.svg"
# MAX_NONFOCUS = "max-1.svg"

# GRAY = "_gray.svg"


# class TitleBtn(SvgBtn):
#     _clicked = pyqtSignal()

#     def __init__(self, focused: str, nonfocused: str, size: int):
#         self.focused = focused
#         self.nonfocused = nonfocused
#         path = os.path.join(IMAGES_FOLDER, self.nonfocused)
#         super().__init__(icon_path = path, size = size, parent=None)
        
#     def set_focused(self):
#         path = os.path.join(IMAGES_FOLDER, self.focused)
#         self.set_icon(path)

#     def set_nonfocused(self):
#         path = os.path.join(IMAGES_FOLDER, self.nonfocused)
#         self.set_icon(path)

#     def disable_(self):
#         path = os.path.join(IMAGES_FOLDER, JsonData.theme + GRAY)
#         self.setDisabled(True)
#         self.set_icon(path)

#     def mousePressEvent(self, a0: QMouseEvent | None) -> None:
#         self._clicked.emit()


# class TitleBtns(QWidget):
#     def __init__(self):
#         super().__init__()

#         h_lay = LayoutHor()
#         h_lay.setSpacing(10)
#         self.setLayout(h_lay)

#         h_lay.addSpacerItem(QSpacerItem(10, 0))

#         self.title_btns: list[TitleBtn] = []

#         self.close_btn = TitleBtn(CLOSE_FOCUS, CLOSE_NONFOCUS, 13)
#         self.title_btns.append(self.close_btn)
#         h_lay.addWidget(self.close_btn)

#         self.min_btn = TitleBtn(MIN_FOCUS, MIN_NONFOCUS, 13)
#         self.title_btns.append(self.min_btn)
#         h_lay.addWidget(self.min_btn)

#         self.max_btn = TitleBtn(MAX_FOCUS, MAX_NONFOCUS, 13)
#         self.title_btns.append(self.max_btn)
#         h_lay.addWidget(self.max_btn)

#         h_lay.addSpacerItem(QSpacerItem(10, 0))

#         self.adjustSize()
#         self.setFixedWidth(self.width())

#     def enterEvent(self, a0: QEvent | None) -> None:
#         for i in self.title_btns:
#             if i.isEnabled():
#                 i.set_focused()
    
#     def leaveEvent(self, a0: QEvent | None) -> None:
#         for i in self.title_btns:
#             if i.isEnabled():
#                 i.set_nonfocused()


# class TitleBar(QFrame):
#     def __init__(self, parent: QMainWindow):
#         super().__init__(parent)

#         self.parent_ = parent
#         self.old_pos = self.pos()

#         self.setFixedHeight(33)

#         self.h_lay = LayoutHor()
#         self.setLayout(self.h_lay)

#         self.title_btns = TitleBtns()
#         self.h_lay.addWidget(self.title_btns)

#         self.title = QLabel()
#         self.h_lay.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)
#         self.h_lay.addSpacerItem(QSpacerItem(self.title_btns.width(), 0))

#     def mousePressEvent(self, a0: QMouseEvent | None) -> None:
#         self.old_pos = a0.globalPos()
#         return super().mousePressEvent(a0)

#     def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
#         delta = QPoint(a0.globalPos() - self.old_pos)
#         self.parent_.move(self.parent_.x() + delta.x(), self.parent_.y() + delta.y())
#         self.old_pos = a0.globalPos()
#         return super().mouseMoveEvent(a0)


class Manager:
    wins: list[QMainWindow] = []


class WinFrameless(QMainWindow):
    def __init__(self, parent: QWidget = None):

        super().__init__(parent=parent)

        central_widget = QWidget()
        central_widget.setContentsMargins(1, 1, 1, 1)
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
        ...

    def disable_max(self):
        ...

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
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # у этого виджета закруглены только нижние углы
        self.content_wid = QFrame()
        self.central_layout_v.addWidget(self.content_wid)

        self.content_lay_v = LayoutVer()
        self.content_lay_v.setContentsMargins(10, 5, 10, 5)
        self.content_wid.setLayout(self.content_lay_v)
