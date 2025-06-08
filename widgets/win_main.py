import os
from typing import Literal

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import (QDesktopWidget, QFrame, QPushButton, QSplitter,
                             QVBoxLayout, QWidget)

from base_widgets import LayoutHor, LayoutVer
from base_widgets.wins import WinFrameless
from cfg import Dynamic, JsonData, Static, ThumbData
from lang import Lang
from main_folders import MainFolder
from paletes import ThemeChanger
from signals import SignalsApp
from utils.scaner import Scaner
from widgets.win_upload import WinUpload

from .bar_bottom import BarBottom
from .bar_macos import BarMacos
from .bar_top import BarTop
from .grid.grid import Grid
from .menu_left import MenuLeft
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


class USep(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: rgba(0, 0, 0, 0.2)")
        self.setFixedHeight(1)


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


        sep_upper = USep()
        right_lay.addWidget(sep_upper)

        grid = Grid()
        right_lay.addWidget(grid)

        sep_bottom = USep()
        right_lay.addWidget(sep_bottom)

        bar_bottom = BarBottom()
        bar_bottom.theme_changed.connect(grid.reload_rubber)
        right_lay.addWidget(bar_bottom)

        # Добавляем splitter в основной layout
        h_lay_main.addWidget(splitter)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([Static.MENU_LEFT_WIDTH, self.width() - Static.MENU_LEFT_WIDTH])

        ThemeChanger.start()

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

            main_folder = MainFolder.current.name.capitalize()

            if Dynamic.curr_coll_name == Static.NAME_ALL_COLLS:
                t = Lang.all_colls

            elif Dynamic.curr_coll_name == Static.NAME_FAVS:
                t = Lang.fav_coll

            else:
                t = Dynamic.curr_coll_name

            if Dynamic.resents:
                t = Lang.recents

            t = f"{main_folder}: {t}"

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
        MainFolder.current.set_current_path()
        coll_folder = MainFolder.current.get_current_path()
        if not coll_folder:
            self.open_smb_win()

    def open_smb_win(self):
        self.smb_win = WinSmb()
        self.smb_win.adjustSize()
        self.smb_win.center_relative_parent(self)
        self.smb_win.show()

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
                if Dynamic.thumb_size_ind < len(ThumbData.PIXMAP_SIZE) - 1:
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
        MainFolder.current.set_current_path()
        coll_folder = MainFolder.current.get_current_path()
        if not coll_folder:
            self.open_smb_win()
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