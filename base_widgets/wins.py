from PyQt5.QtCore import QEvent, QPoint, Qt
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

        self.close_btn = SvgBtn("close-1.svg", 13)
        btn_layout.addWidget(self.close_btn)

        self.min_btn = SvgBtn("min-1.svg", 13)
        btn_layout.addWidget(self.min_btn)

        self.max_btn = SvgBtn("max-1.svg", 13)
        btn_layout.addWidget(self.max_btn)

        btn_layout.addSpacerItem(QSpacerItem(10, 0))

        self.adjustSize()
        self.setFixedWidth(self.width())

        self.installEventFilter(self)

    def symbolic_icons(self):
        self.close_btn.set_icon("close-2.svg")
        if self.min_btn.isEnabled():
            self.min_btn.set_icon("min-2.svg")
            self.max_btn.set_icon("max-2.svg")

    def non_symbolic_icons(self):
        self.close_btn.set_icon("close-1.svg")
        if self.min_btn.isEnabled():
            self.min_btn.set_icon("min-1.svg")
            self.max_btn.set_icon("max-1.svg")

    def eventFilter(self, source, event):
        if event.type() == QEvent.Enter:
            self.symbolic_icons()

        elif event.type() == QEvent.Leave:
            self.non_symbolic_icons()

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
        self.main_layout.addWidget(self.title, alignment=Qt.AlignCenter)
        self.main_layout.addSpacerItem(QSpacerItem(self.btns.width(), 0))

        self.oldPos = self.pos()
        self.show()

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.my_win.move(self.my_win.x() + delta.x(), self.my_win.y() + delta.y())
        self.oldPos = event.globalPos()

    def add_r_wid(self, wid: QWidget):
        self.main_layout.addWidget(wid)

        self.title.setStyleSheet(
            f"""
            padding-left: {wid.width()}px;
            """)


class WinBase(QMainWindow):
    def __init__(self, close_func: callable, parent=None):
        super().__init__(parent=parent)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.rect()
        self.grips[1].move(rect.right() - self.gripSize, 0)
        self.grips[2].move(
            rect.right() - self.gripSize, rect.bottom() - self.gripSize)
        self.grips[3].move(0, rect.bottom() - self.gripSize)

    def center_win(self, parent: QMainWindow = None):
        if not parent:
            parent = MainUtils.get_central_widget()

        geo = self.geometry()
        geo.moveCenter(parent.geometry().center())
        self.setGeometry(geo)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.deleteLater()
        super().keyPressEvent(event)

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

    def disable_min_max(self):
        self.titlebar.btns.min_btn.setDisabled(True)
        self.titlebar.btns.min_btn.set_icon("gray-2.svg")
        self.titlebar.btns.max_btn.setDisabled(True)
        self.titlebar.btns.max_btn.set_icon("gray-2.svg")


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