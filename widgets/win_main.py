from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import (QDesktopWidget, QFrame, QPushButton, QVBoxLayout,
                             QWidget)

from base_widgets import LayoutHor, LayoutVer, WinBase
from cfg import ALL_COLLS, Dynamic, JsonData
from signals import SignalsApp
from styles import Names, Themes
from utils.main_utils import MainUtils
from utils.scaner import Scaner

from .bar_bottom import BarBottom
from .bar_macos import BarMacos
from .bar_top import BarTop
from .grid.grid import Grid
from .menu_left import MenuLeft
from .wid_notification import Notification
from .wid_search import WidSearch
from .win_smb import WinSmb


class TestWid(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(100, 100)
        self.setStyleSheet("background: black;")

        v_layout = QVBoxLayout()
        self.setLayout(v_layout)

        btn = QPushButton('test btn')
        v_layout.addWidget(btn)
        btn.clicked.connect(self.reload)

    def reload(self):
        ...


class WinMain(WinBase):
    def __init__(self):
        super().__init__(close_func=self.my_close_event)

        self.setContentsMargins(0, 0, 0, 0)
        self.resize(JsonData.root_g["aw"], JsonData.root_g["ah"])
        self.setMenuBar(BarMacos())
        self.titlebar.add_r_wid(WidSearch())
        self.set_title(
            Dynamic.lng.all_colls
            if JsonData.curr_coll == ALL_COLLS
            else JsonData.curr_coll
            )

        h_wid_main = QWidget()
        h_lay_main = LayoutHor()
        h_wid_main.setLayout(h_lay_main)
        self.central_layout.addWidget(h_wid_main)

        left_wid = MenuLeft()
        h_lay_main.addWidget(left_wid)

        mid_wid = QFrame()
        mid_wid.setFixedWidth(1)
        mid_wid.setObjectName(Names.separator)
        mid_wid.setStyleSheet(Themes.current)
        h_lay_main.addWidget(mid_wid)

        right_wid = QWidget()
        h_lay_main.addWidget(right_wid)
        right_lay = LayoutVer()
        right_wid.setLayout(right_lay)

        self.bar_top = BarTop()
        right_lay.addWidget(self.bar_top)
        self.bar_top.resizeEvent = self.resize_noti_cmd

        grid = Grid()
        right_lay.addWidget(grid)

        bar_bottom = BarBottom()
        right_lay.addWidget(bar_bottom)

        self.noti = Notification(parent=right_wid)
        self.noti.move(2, 2)
        self.noti.hide()

        SignalsApp.all.win_main_cmd.connect(self.win_main_cmd)
        QTimer.singleShot(100, self.after_start)
        grid.setFocus()

    def resize_noti_cmd(self, *args):
        w, h = self.bar_top.width(), self.bar_top.height()
        self.noti.resize(w - 6, h - 6)

    def win_main_cmd(self, flag: str):
        if flag == "show":
            self.show()
        elif flag == "exit":
            self.on_exit()
        elif flag == "set_title":
            self.set_title(
                Dynamic.lng.all_colls
                if JsonData.curr_coll == ALL_COLLS
                else JsonData.curr_coll
                )
        else: 
            raise Exception("app > win main > wrong flag", flag)

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
    
    def my_close_event(self, a0: QCloseEvent | None) -> None:
        self.titlebar.btns.nonfocused_icons()
        self.hide()
        a0.ignore()

    def on_exit(self):
        Scaner.app.stop()
        geo = self.geometry()
        JsonData.root_g.update({"aw": geo.width(), "ah": geo.height()})
        JsonData.write_json_data()

    def after_start(self):
        Scaner.app.start()

        if not MainUtils.smb_check():
            self.smb_win = WinSmb(parent=self)
            self.smb_win.show()

        # self.test = TestWid()
        # self.test.setWindowModality(Qt.WindowModality.ApplicationModal)
        # self.test.show()
    
    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_W:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.my_close_event(a0)

        elif a0.key() == Qt.Key.Key_F:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                SignalsApp.all.wid_search_cmd.emit("focus")

        elif a0.key() == Qt.Key.Key_Escape:
            a0.ignore()

        elif a0.key() == Qt.Key.Key_Equal:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if JsonData.curr_size_ind < 3:
                    JsonData.curr_size_ind += 1
                    SignalsApp.all.slider_change_value.emit(JsonData.curr_size_ind)

        elif a0.key() == Qt.Key.Key_Minus:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if JsonData.curr_size_ind > 0:
                    JsonData.curr_size_ind -= 1
                    SignalsApp.all.slider_change_value.emit(JsonData.curr_size_ind)
