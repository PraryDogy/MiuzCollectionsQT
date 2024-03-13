from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAction, QDesktopWidget, QFrame, QMainWindow,
                             QSpacerItem, QWidget)

from base_widgets import BaseEmptyWin, LayoutH, LayoutV
from cfg import cnf
from signals import gui_signals_app

from ..filters_bar import FiltersBar
from ..left_menu import LeftMenu
from ..menu_bar import MacMenuBar
from ..search_bar import SearchBar
from ..st_bar import StBar
from ..thumbnails import Thumbnails


class Manager:
    smb_win = None


class RightWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        v_layout = LayoutV(self)

        self.filters_bar = FiltersBar()

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: black;")

        self.thumbnails = Thumbnails()
        self.st_bar = StBar()

        v_layout.addWidget(self.filters_bar)
        v_layout.addWidget(sep)
        v_layout.addWidget(self.thumbnails)
        v_layout.addWidget(self.st_bar)


class ContentWid(QWidget):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        h_layout = LayoutH(self)

        self.left_menu = LeftMenu()

        vertical_separator = QFrame()
        vertical_separator.setFixedWidth(1)
        vertical_separator.setStyleSheet("background-color: black;")

        self.right_widget = RightWidget()

        h_layout.addWidget(self.left_menu)
        h_layout.addWidget(vertical_separator)
        h_layout.addWidget(self.right_widget)


class WinMain(BaseEmptyWin):
    def __init__(self):
        super().__init__(close_func=self.mycloseEvent)

        self.setContentsMargins(0, 0, 0, 0)
        self.setFocus()
        self.setWindowTitle(cnf.app_name)
        self.resize(cnf.root_g["aw"], cnf.root_g["ah"])
        self.center()

        menubar = MacMenuBar()
        self.setMenuBar(menubar)

        search_bar = SearchBar()
        self.titlebar.add_r_wid(search_bar)

        self.set_title(self.check_coll())
        gui_signals_app.reload_title.connect(self.reload_title)

        content_wid = ContentWid()
        self.base_layout.addWidget(content_wid)

        # что делать при выходе
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)

        # Подключение методов к главному окну
        self.keyPressEvent = self.mykeyPressEvent

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def mycloseEvent(self, event):
        if event.spontaneous():
            self.hide()
            event.ignore()

    def mykeyPressEvent(self, event):
        if event.key() == Qt.Key_W:
            if event.modifiers() == Qt.ControlModifier:
                self.hide()

        if event.key() == Qt.Key_F:
            if event.modifiers() == Qt.ControlModifier:
                gui_signals_app.set_focus_search.emit()

        else:
            super(QMainWindow, self).keyPressEvent(event)

    def reload_title(self):
        self.set_title(self.check_coll())

    def check_coll(self) -> str:
        if cnf.curr_coll == cnf.ALL_COLLS:
            return cnf.lng.all_colls
        elif cnf.curr_coll == cnf.RECENT_COLLS:
            return cnf.lng.recents
        else:
            return cnf.curr_coll