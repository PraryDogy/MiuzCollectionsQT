import os

from PyQt5.QtCore import QEvent, QObject, QPoint, Qt, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QFocusEvent, QKeyEvent, QMouseEvent, QResizeEvent
from PyQt5.QtWidgets import (QFrame, QLabel, QMainWindow, QSizeGrip,
                             QSpacerItem, QWidget)

from cfg import cnf
from styles import Names, Themes
from utils import MainUtils

from .layouts import LayoutH, LayoutV
from .svg_btn import SvgBtn


class Btns(QWidget):
    def __init__(self):
        super().__init__()

        btn_layout = LayoutH()
        btn_layout.setSpacing(10)
        self.setLayout(btn_layout)

        btn_layout.addSpacerItem(QSpacerItem(10, 0))

        self.close_btn = SvgBtn(os.path.join("images", "close-1.svg"), 13)
        btn_layout.addWidget(self.close_btn)

        self.min_btn = SvgBtn(os.path.join("images", "min-1.svg"), 13)
        btn_layout.addWidget(self.min_btn)

        self.max_btn = SvgBtn(os.path.join("images", "max-1.svg"), 13)
        btn_layout.addWidget(self.max_btn)

        btn_layout.addSpacerItem(QSpacerItem(10, 0))

        self.adjustSize()
        self.setFixedWidth(self.width())

        self.installEventFilter(self)

    def focused_icons(self):
        if self.close_btn.isEnabled():
            self.close_btn.set_icon(os.path.join("images", "close-2.svg"))

        if self.min_btn.isEnabled():
            self.min_btn.set_icon(os.path.join("images", "min-2.svg"))
            self.max_btn.set_icon(os.path.join("images", "max-2.svg"))

    def nonfocused_icons(self):
        if self.close_btn.isEnabled():
            self.close_btn.set_icon(os.path.join("images", "close-1.svg"))

        if self.min_btn.isEnabled():
            self.min_btn.set_icon(os.path.join("images", "min-1.svg"))
            self.max_btn.set_icon(os.path.join("images", "max-1.svg"))

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

        self.main_layout = LayoutH()
        self.setLayout(self.main_layout)

        self.btns = Btns()
        self.main_layout.addWidget(self.btns)

        self.title = QLabel()
        self.main_layout.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addSpacerItem(QSpacerItem(self.btns.width(), 0))

        self.oldPos = self.pos()
        self.show()

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        self.oldPos = a0.globalPos()
        return super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        delta = QPoint(a0.globalPos() - self.oldPos)
        self.my_win.move(self.my_win.x() + delta.x(), self.my_win.y() + delta.y())
        self.oldPos = a0.globalPos()
        return super().mouseMoveEvent(a0)

    def add_r_wid(self, wid: QWidget):
        self.main_layout.addWidget(wid)

        self.title.setStyleSheet(
            f"""
            padding-left: {wid.width()}px;
            """)


class Manager:
    wins = []


class WinBase(QMainWindow, QObject):
    def __init__(self, close_func: callable, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        central_widget = QWidget()
        central_widget.setContentsMargins(1, 1, 1, 1)
        central_widget.setObjectName(Names.central_widget)
        central_widget.setStyleSheet(Themes.current)

        self.setCentralWidget(central_widget)
        self.central_layout = LayoutV(central_widget)

        self.titlebar = TitleBar(self)
        self.titlebar.btns.max_btn.mouseReleaseEvent = self.toggle_fullscreen
        self.titlebar.btns.min_btn.mouseReleaseEvent = lambda e: self.showMinimized()
        self.titlebar.btns.close_btn.mouseReleaseEvent = close_func
        self.central_layout.addWidget(self.titlebar)

        self.gripSize = 16
        self.grips = []
        for i in range(4):
            grip = QSizeGrip(self)
            grip.resize(self.gripSize, self.gripSize)
            self.grips.append(grip)

        Manager.wins.append(self)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        try:
            main_win = MainUtils.get_main_win()
            if main_win.isHidden():
                main_win.show()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

        try:
            Manager.wins.remove(self)
            self.deleteLater()
        except Exception as e:
            pass

        return super().closeEvent(a0)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        return super().mouseReleaseEvent(a0)

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
    
    def center_win(self, parent: QWidget):
        try:
            geo = self.geometry()
            geo.moveCenter(parent.window().geometry().center())
            self.setGeometry(geo)
        except (RuntimeError, Exception) as e:
            MainUtils.print_err(parent=self, error=e)

    def fit_size(self):
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

    def toggle_fullscreen(self, event):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def set_title(self, text):
        self.titlebar.title.setText(text)

    def disable_min(self):
        self.titlebar.btns.min_btn.setDisabled(True)
        self.titlebar.btns.min_btn.set_icon(os.path.join("images", f"{cnf.theme}_gray.svg"))

    def disable_max(self):
        self.titlebar.btns.max_btn.setDisabled(True)
        self.titlebar.btns.max_btn.set_icon(os.path.join("images", f"{cnf.theme}_gray.svg"))

    def disable_close(self):
        self.titlebar.btns.close_btn.setDisabled(True)
        self.titlebar.btns.close_btn.set_icon(os.path.join("images", f"{cnf.theme}_gray.svg"))


class BaseBottomWid(QFrame):
    def __init__(self, left=10, top=10, right=10, bottom=10):
        super().__init__()
        self.setContentsMargins(left, top, right, bottom)
        self.setObjectName(Names.base_bottom_widget)
        self.setStyleSheet(Themes.current)


class WinStandartBase(WinBase):
    def __init__(self, close_func: callable):
        super().__init__(close_func)
        self.titlebar.setFixedHeight(28)

        self.content_wid = BaseBottomWid()
        self.central_layout.addWidget(self.content_wid)

        self.content_layout = LayoutV()
        self.content_wid.setLayout(self.content_layout)
    

class WinImgViewBase(WinBase):
    def __init__(self, close_func: callable):
        super().__init__(close_func)

        self.titlebar.setFixedHeight(28)

        self.content_wid = BaseBottomWid(left=10, top=0, right=10, bottom=0)
        self.central_layout.addWidget(self.content_wid)
        self.content_wid.setObjectName("img_view_bg")
        self.content_wid.setStyleSheet(Themes.current)

        self.content_layout = LayoutV()
        self.content_wid.setLayout(self.content_layout)

    def bind_content_wid(self, func: callable):
        self.content_wid.mouseReleaseEvent = func


class WinSmallBase(WinBase):
    def __init__(self, close_func: callable):
        super().__init__(close_func)

        self.titlebar.setFixedHeight(28)

        self.content_wid = BaseBottomWid(left=10, top=5, right=10, bottom=7)
        self.central_layout.addWidget(self.content_wid)

        self.content_layout = LayoutV()
        self.content_wid.setLayout(self.content_layout)