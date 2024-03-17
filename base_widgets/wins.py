from PyQt5.QtCore import QEvent, QPoint, Qt, pyqtSignal
from PyQt5.QtWidgets import (QFrame, QLabel, QMainWindow, QSizeGrip,
                             QSpacerItem, QWidget)

from signals import gui_signals_app
from styles import Styles
from utils import MainUtils

from .svg_btn import SvgBtn
from .layouts import LayoutH, LayoutV


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


class CustomTitleBar(QFrame):
    def __init__(self, win: QMainWindow):
        super().__init__(win)
        self.my_win = win
        self.setFixedHeight(33)
        self.setStyleSheet(
            f"""
            background: {Styles.st_bar_bg_color};
            border-top-right-radius: {Styles.base_radius}px;
            border-top-left-radius: {Styles.base_radius}px;
            """)

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


class BaseEmptyWin(QMainWindow):
    was_closed = pyqtSignal()

    def __init__(self, close_func: callable):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        zero_layout = LayoutV(main_widget)

        border_wid = QWidget()
        border_wid.setContentsMargins(1, 1, 1, 1)
        border_wid.setObjectName("border_wid")
        border_wid.setStyleSheet(
            f"""
            #border_wid 
                {{
                border-radius: {Styles.base_radius}px;
                background: {Styles.menu_sel_item_color}
                }}
            """)
        zero_layout.addWidget(border_wid)

        self.base_layout = LayoutV()
        border_wid.setLayout(self.base_layout)

        self.titlebar = CustomTitleBar(self)
        self.titlebar.btns.max_btn.mouseReleaseEvent = self.toggle_fullscreen
        self.titlebar.btns.min_btn.mouseReleaseEvent = lambda e: self.showMinimized()
        self.titlebar.btns.close_btn.mouseReleaseEvent = close_func
        self.base_layout.addWidget(self.titlebar)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: black;")
        self.base_layout.addWidget(sep)

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
            gui_signals_app.set_focus_viewer.emit()
        super().keyPressEvent(event)

    def fit_size(self):
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

    def toggle_fullscreen(self, event):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def set_title(self, text):
        self.titlebar.title.setText(text)

    def disable_min_max(self):
        self.titlebar.btns.min_btn.setDisabled(True)
        self.titlebar.btns.min_btn.set_icon("gray-2.svg")
        self.titlebar.btns.max_btn.setDisabled(True)
        self.titlebar.btns.max_btn.set_icon("gray-2.svg")


class BaseBottomWid(QFrame):
    def __init__(self, bg=Styles.base_bg_color, left=10, top=10, right=10, bottom=10):
        super().__init__()
        self.setContentsMargins(left, top, right, bottom)
        self.setStyleSheet(
            f"""
            background: {bg};
            border: 0px;
            border-bottom-left-radius: {Styles.base_radius}px;
            border-bottom-right-radius: {Styles.base_radius}px;
            """)


class Manager:
    wins = []


class WinAutoRemove(BaseEmptyWin):
    delete_win = pyqtSignal()

    def __init__(self, close_func: callable):
        super().__init__(close_func)
        Manager.wins.append(self)
        self.delete_win.connect(self.delete_win_cmd)

    def delete_win_cmd(self):
        try:
            Manager.wins.remove(self)
        except ValueError:
            print("delete win: win not in manager.wins")

    def closeEvent(self, event):
        self.delete_win.emit()
        super().closeEvent(event)


class WinStandartBase(WinAutoRemove):
    delete_win = pyqtSignal()
    
    def __init__(self, close_func: callable):
        super().__init__(close_func)
        self.titlebar.setFixedHeight(28)

        self.content_wid = BaseBottomWid()
        self.base_layout.addWidget(self.content_wid)

        self.content_layout = LayoutV()
        self.content_wid.setLayout(self.content_layout)
    

class WinImgViewBase(WinAutoRemove):
    def __init__(self, close_func: callable):
        super().__init__(close_func)

        self.titlebar.setFixedHeight(28)

        # zoom widget top right corner

        # btn_w = 40
        # svg_w = 20
        # r_spacer = 10

        # zoom_wid = QWidget()
        # zoom_wid.setStyleSheet(f"""background-color: transparent;""")
        # zoom_wid.setFixedWidth(btn_w * 3 + r_spacer)

        # zoom_layout = LayoutH()
        # zoom_wid.setLayout(zoom_layout)

        # self.zoom_out = SvgBtn("zoom_out.svg", svg_w)
        # self.zoom_out.setFixedWidth(btn_w)
        # zoom_layout.addWidget(self.zoom_out)

        # self.zoom_in = SvgBtn("zoom_in.svg", svg_w)
        # self.zoom_in.setFixedWidth(btn_w)
        # zoom_layout.addWidget(self.zoom_in)

        # self.zoom_fit = SvgBtn("zoom_fit.svg", svg_w)
        # self.zoom_fit.setFixedWidth(btn_w)
        # zoom_layout.addWidget(self.zoom_fit)

        # fake = QWidget()
        # fake.setFixedWidth(r_spacer)
        # fake.setStyleSheet(f"""background-color: transparent;""")
        # zoom_layout.addWidget(fake)

        # self.titlebar.add_r_wid(zoom_wid)

        # end zoom

        self.content_wid = BaseBottomWid(left=10, top=0, right=10, bottom=0)
        self.base_layout.addWidget(self.content_wid)

        self.content_layout = LayoutV()
        self.content_wid.setLayout(self.content_layout)

    def bind_content_wid(self, func: callable):
        self.content_wid.mouseReleaseEvent = func

    # def bind_zoom(self, zoom_in: callable, zoom_out: callable, zoom_fit: callable):
    #     self.zoom_in.mouseReleaseEvent = zoom_in
    #     self.zoom_out.mouseReleaseEvent = zoom_out
    #     self.zoom_fit.mouseReleaseEvent = zoom_fit


class WinSmallBase(WinAutoRemove):
    def __init__(self, close_func: callable):
        super().__init__(close_func)

        self.titlebar.setFixedHeight(28)

        self.content_wid = BaseBottomWid(left=10, top=5, right=10, bottom=7)
        self.base_layout.addWidget(self.content_wid)

        self.content_layout = LayoutV()
        self.content_wid.setLayout(self.content_layout)