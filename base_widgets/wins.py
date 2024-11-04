import os

from PyQt5.QtCore import QEvent, QObject, QPoint, Qt
from PyQt5.QtGui import QCloseEvent, QKeyEvent, QMouseEvent, QResizeEvent
from PyQt5.QtWidgets import (QFrame, QLabel, QMainWindow, QSizeGrip,
                             QSpacerItem, QWidget)

from cfg import JsonData
from styles import Names, Themes
from utils.main_utils import MainUtils

from .layouts import LayoutHor, LayoutVer
from .svg_btn import SvgBtn

IMAGES_FOLDER = "images"

CLOSE_FOCUS = "close-2.svg"
CLOSE_NONFOCUS = "close-1.svg"

MIN_FOCUS = "min-2.svg"
MIN_NONFOCUS = "min-1.svg"

MAX_FOCUS = "max-2.svg"
MAX_NONFOCUS = "max-1.svg"


class TitleBtn(SvgBtn):
    def __init__(self, focused: str, nonfocused: str, size: int):
        self.focused = focused
        self.nonfocused = nonfocused
        path = os.path.join(IMAGES_FOLDER, self.nonfocused)
        super().__init__(icon_path = path, size = size, parent=None)
        
    def focused(self):
        path = os.path.join(IMAGES_FOLDER, self.focused)
        self.set_icon(path)

    def nonfocused(self):
        path = os.path.join(IMAGES_FOLDER, self.nonfocused)
        self.set_icon(path)


class Btns(QWidget):
    def __init__(self):
        super().__init__()

        h_lay = LayoutHor()
        h_lay.setSpacing(10)
        self.setLayout(h_lay)

        h_lay.addSpacerItem(QSpacerItem(10, 0))

        self.close_btn = TitleBtn(CLOSE_FOCUS, CLOSE_NONFOCUS, 13)
        h_lay.addWidget(self.close_btn)

        self.min_btn = TitleBtn(MIN_FOCUS, MIN_NONFOCUS, 13)
        h_lay.addWidget(self.min_btn)

        self.max_btn = TitleBtn(MAX_FOCUS, MAX_NONFOCUS, 13)
        h_lay.addWidget(self.max_btn)

        h_lay.addSpacerItem(QSpacerItem(10, 0))

        self.adjustSize()
        self.setFixedWidth(self.width())

        self.installEventFilter(self)

    def focused_icons(self):
        if self.close_btn.isEnabled():
            self.close_btn.focused()

        if self.min_btn.isEnabled():
            self.min_btn.focused()
            self.max_btn.focused()

    def nonfocused_icons(self):
        if self.close_btn.isEnabled():
            self.close_btn.nonfocused()

        if self.min_btn.isEnabled():
            self.min_btn.nonfocused()
            self.max_btn.nonfocused()

    def eventFilter(self, source, event):
        if event.type() == QEvent.Enter:
            self.focused_icons()

        elif event.type() == QEvent.Leave:
            self.nonfocused_icons()

        return super().eventFilter(source, event)


class TitleBar(QFrame):
    def __init__(self, win: QMainWindow):
        super().__init__(win)
        self.my_win = win
        self.setFixedHeight(33)
        self.setObjectName(Names.title_bar)
        self.setStyleSheet(Themes.current)

        self.h_lay = LayoutHor()
        self.setLayout(self.h_lay)

        self.btns = Btns()
        self.h_lay.addWidget(self.btns)

        self.title = QLabel()
        self.h_lay.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.h_lay.addSpacerItem(QSpacerItem(self.btns.width(), 0))

        self.oldPos = self.pos()
        self.show()

    def add_r_wid(self, wid: QWidget):
        self.h_lay.addWidget(wid)
        self.title.setStyleSheet(f"""padding-left: {wid.width()}px;""")

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        self.oldPos = a0.globalPos()
        return super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        delta = QPoint(a0.globalPos() - self.oldPos)
        self.my_win.move(self.my_win.x() + delta.x(), self.my_win.y() + delta.y())
        self.oldPos = a0.globalPos()
        return super().mouseMoveEvent(a0)


class Manager:
    wins = []


class WinFrameless(QMainWindow, QObject):
    def __init__(self, close_func: callable, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        central_widget = QWidget()
        central_widget.setContentsMargins(1, 1, 1, 1)
        central_widget.setObjectName(Names.central_widget)
        central_widget.setStyleSheet(Themes.current)

        self.setCentralWidget(central_widget)
        self.central_layout_v = LayoutVer(central_widget)

        self.titlebar = TitleBar(self)
        self.titlebar.btns.max_btn.mouseReleaseEvent = self.toggle_fullscreen
        self.titlebar.btns.min_btn.mouseReleaseEvent = self.show_minimized
        self.titlebar.btns.close_btn.mouseReleaseEvent = close_func
        self.central_layout_v.addWidget(self.titlebar)

        self.gripSize = 16
        self.grips = []
        for i in range(4):
            grip = QSizeGrip(self)
            grip.resize(self.gripSize, self.gripSize)
            self.grips.append(grip)

        Manager.wins.append(self)

    def center_relative_parent(self, parent: QWidget):
        try:
            geo = self.geometry()
            geo.moveCenter(parent.window().geometry().center())
            self.setGeometry(geo)
        except (RuntimeError, Exception) as e:
            MainUtils.print_err(parent=self, error=e)

    def toggle_fullscreen(self, *args):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def show_minimized(self, *args):
        self.showMinimized()

    def set_title(self, text):
        self.titlebar.title.setText(text)

    def disable_min(self):
        self.titlebar.btns.min_btn.setDisabled(True)
        self.titlebar.btns.min_btn.set_icon(os.path.join("images", f"{JsonData.theme}_gray.svg"))

    def disable_max(self):
        self.titlebar.btns.max_btn.setDisabled(True)
        self.titlebar.btns.max_btn.set_icon(os.path.join("images", f"{JsonData.theme}_gray.svg"))

    def disable_close(self):
        self.titlebar.btns.close_btn.setDisabled(True)
        self.titlebar.btns.close_btn.set_icon(os.path.join("images", f"{JsonData.theme}_gray.svg"))

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        try:
            Manager.wins.remove(self)
            self.deleteLater()
        except Exception as e:
            pass

        return super().closeEvent(a0)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        rect = self.rect()
        self.grips[1].move(rect.right() - self.gripSize, 0)
        self.grips[2].move(
            rect.right() - self.gripSize, rect.bottom() - self.gripSize)
        self.grips[3].move(0, rect.bottom() - self.gripSize)
        return super().resizeEvent(a0)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.close()
        return super().keyPressEvent(a0)
    

class BaseBottomWid(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName(Names.base_bottom_widget)
        self.setStyleSheet(Themes.current)


class WinStandartBase(WinFrameless):
    def __init__(self, close_func: callable):
        super().__init__(close_func)
        self.titlebar.setFixedHeight(28)
        self.content_wid = BaseBottomWid()
        self.central_layout_v.addWidget(self.content_wid)
        self.content_layout = LayoutVer()
        self.content_wid.setLayout(self.content_layout)
    

class WinImgViewBase(WinFrameless):
    def __init__(self, close_func: callable):
        super().__init__(close_func)
        self.titlebar.setFixedHeight(28)
        self.content_wid = BaseBottomWid()
        self.content_wid.setContentsMargins(10, 0, 10, 0)
        self.central_layout_v.addWidget(self.content_wid)
        self.content_wid.setObjectName("img_view_bg")
        self.content_wid.setStyleSheet(Themes.current)
        self.content_layout = LayoutVer()
        self.content_wid.setLayout(self.content_layout)


class WinSmallBase(WinFrameless):
    def __init__(self, close_func: callable):
        super().__init__(close_func)
        self.titlebar.setFixedHeight(28)
        self.content_wid = BaseBottomWid()
        self.content_wid.setContentsMargins(10, 5, 10, 5)
        self.central_layout_v.addWidget(self.content_wid)
        self.content_layout = LayoutVer()
        self.content_wid.setLayout(self.content_layout)