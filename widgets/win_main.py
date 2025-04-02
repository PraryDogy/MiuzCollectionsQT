import os
from typing import Literal

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import (QDesktopWidget, QFrame, QPushButton, QVBoxLayout,
                             QWidget, QSplitter)

from base_widgets import LayoutHor, LayoutVer
from base_widgets.wins import WinFrameless
from main_folders import MainFolder
from cfg import Dynamic, JsonData, Static
from lang import Lang
from signals import SignalsApp
from utils.scaner import Scaner
from utils.utils import Utils
from widgets.win_upload import WinUpload

from .actions import OpenWins
from .bar_bottom import BarBottom
from .bar_macos import BarMacos
from .bar_top import BarTop
from .grid.grid import Grid
from .menu_left import MenuLeft


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


class WinMain(WinFrameless):
    def __init__(self):
        super().__init__()

        self.setAcceptDrops(True)

        self.resize(Dynamic.root_g["aw"], Dynamic.root_g["ah"])
        self.setMinimumWidth(750)
        self.setMenuBar(BarMacos())

        h_wid_main = QWidget()
        h_lay_main = LayoutHor()
        h_lay_main.setContentsMargins(0, 0, 5, 0)
        h_wid_main.setLayout(h_lay_main)
        self.central_layout.addWidget(h_wid_main)

        # Создаем QSplitter
        splitter = QSplitter(Qt.Horizontal)

        # Левый виджет (MenuLeft)
        left_wid = MenuLeft()
        splitter.addWidget(left_wid)

        # Правый виджет
        right_wid = QWidget()
        splitter.addWidget(right_wid)
        right_lay = LayoutVer()
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_wid.setLayout(right_lay)

        # Добавляем элементы в правую панель
        self.bar_top = BarTop()
        right_lay.addWidget(self.bar_top)

        grid = Grid()
        right_lay.addWidget(grid)

        bar_bottom = BarBottom()
        right_lay.addWidget(bar_bottom)

        # Добавляем splitter в основной layout
        h_lay_main.addWidget(splitter)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([Static.MENU_LEFT_WIDTH, self.width() - Static.MENU_LEFT_WIDTH])

        SignalsApp.instance.win_main_cmd.connect(self.win_main_cmd)
        SignalsApp.instance.win_main_cmd.emit("set_title")
        QTimer.singleShot(100, self.after_start)
        grid.setFocus()

    def win_main_cmd(self, flag: Literal["show", "exit", "set_title"]):

        if flag == "show":
            self.show()

        elif flag == "exit":
            self.on_exit()

        elif flag == "set_title":

            if Dynamic.curr_coll_name == Static.NAME_ALL_COLLS:
                t = Lang.all_colls

            elif Dynamic.curr_coll_name == Static.NAME_FAVS:
                t = Lang.fav_coll

            else:
                t = Dynamic.curr_coll_name

            if Dynamic.resents:
                t = Lang.recents

            self.setWindowTitle(t)

        else: 
            raise Exception("app > win main > wrong flag", flag)

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
    
    def hide_(self, *args):
        self.hide()

    def on_exit(self):
        Scaner.stop()
        JsonData.write_json_data()

    def after_start(self):
        Scaner.start()
        coll_folder = Utils.get_main_folder_path(main_folder=MainFolder.current)
        if not coll_folder:
            OpenWins.smb(self)

        # from .actions import OpenWins
        # OpenWins.smb(parent_=self)
        # self.test = TestWid()
        # self.test.setWindowModality(Qt.WindowModality.ApplicationModal)
        # self.test.show()

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.hide()
        a0.ignore()
    
    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_W:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.hide_(a0)

        elif a0.key() == Qt.Key.Key_F:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                SignalsApp.instance.wid_search_cmd.emit("focus")

        elif a0.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
                self.raise_()
            else:
                a0.ignore()

        elif a0.key() == Qt.Key.Key_Equal:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if Dynamic.thumb_size_ind < 3:
                    Dynamic.thumb_size_ind += 1
                    SignalsApp.instance.slider_change_value.emit(Dynamic.thumb_size_ind)

        elif a0.key() == Qt.Key.Key_Minus:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if Dynamic.thumb_size_ind > 0:
                    Dynamic.thumb_size_ind -= 1
                    SignalsApp.instance.slider_change_value.emit(Dynamic.thumb_size_ind)

    def dragEnterEvent(self, a0):
        a0.acceptProposedAction()
        return super().dragEnterEvent(a0)
    
    def dropEvent(self, a0):

        if not a0.mimeData().hasUrls() or a0.source() is not None:
            return

        coll_folder = Utils.get_main_folder_path(main_folder=MainFolder.current)
        if not coll_folder:
            OpenWins.smb(self)
            return

        urls: list[str] = [
            i.toLocalFile()
            for i in a0.mimeData().urls()
            if os.path.isfile(i.toLocalFile())
        ]

        self.win_upload = WinUpload(urls=urls)
        self.win_upload.center_relative_parent(parent=self)
        self.win_upload.show()

        return super().dropEvent(a0)