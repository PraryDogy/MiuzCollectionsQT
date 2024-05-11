import sys

from PyQt5.QtCore import QEvent, Qt, QTimer
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import (QAction, QApplication, QDesktopWidget, QFrame,
                             QMainWindow, QPushButton, QVBoxLayout, QWidget)

from base_widgets import BaseEmptyWin, LayoutH, LayoutV
from cfg import cnf
from signals import gui_signals_app, utils_signals_app
from utils import MainUtils
from widgets import (FiltersBar, LeftMenu, MacMenuBar, Notification, SearchBar,
                     StBar, Thumbnails)


class Manager:
    smb_win = None
    first_load_win = None


class TestWid(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        v_layout = QVBoxLayout()
        self.setLayout(v_layout)

        btn = QPushButton('reload')
        v_layout.addWidget(btn)
        btn.clicked.connect(self.reload)

    def widgets_count(self):
        all_widgets = QApplication.instance().allWidgets()
        return len(all_widgets)

    def reload(self):
        from widgets import win_first_load
        self.abc = win_first_load.WinFirstLoad()
        self.abc.show()
        return

        print(self.widgets_count())
        gui_signals_app.reload_thumbnails.emit()
        print(self.widgets_count())


class RightWidget(QFrame):
    def __init__(self):
        super().__init__()

        v_layout = LayoutV(self)

        self.filters_bar = FiltersBar()
        self.thumbnails = Thumbnails()
        self.st_bar = StBar()

        v_layout.addWidget(self.filters_bar)
        v_layout.addWidget(self.thumbnails)
        v_layout.addWidget(self.st_bar)

        self.notification = Notification(parent=self)
        gui_signals_app.noti_main.connect(self.notification.show_notify)
        self.notification.move(2, 2)
        self.notification.resize(
            self.thumbnails.width() - 6,
            self.filters_bar.height() - 4
            )
        
    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        self.notification.resize(
            self.thumbnails.width() - 6,
            self.filters_bar.height() - 4
            )
        return super().resizeEvent(a0)


class ContentWid(QFrame):
    def __init__(self):
        super().__init__()
        h_layout = LayoutH(self)

        self.left_menu = LeftMenu()
        self.right_widget = RightWidget()

        h_layout.addWidget(self.left_menu)
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
        self.central_layout.addWidget(content_wid)

        # что делать при выходе
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def mycloseEvent(self, event):
        self.titlebar.btns.non_symbolic_icons()
        self.hide()
        event.ignore()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_W:
            if event.modifiers() == Qt.ControlModifier:
                self.mycloseEvent(event)

        elif event.key() == Qt.Key_F:
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
        

class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.setStyleSheet(f"""QLabel {{color: white;}}""")

        self.main_win = WinMain()
        self.main_win.show()

        self.installEventFilter(self)
        self.aboutToQuit.connect(self.on_exit)

        self.after_start_timer = QTimer(self)
        self.after_start_timer.setSingleShot(True)
        self.after_start_timer.timeout.connect(self.after_start)
        self.after_start_timer.start(100)

    def eventFilter(self, obj, event: QEvent):
        if event.type() == QEvent.ApplicationActivate:
            self.main_win.show()
        return super().eventFilter(obj, event)
    
    def on_exit(self):
        utils_signals_app.scaner_stop.emit()

        geo = self.main_win.geometry()

        cnf.root_g.update(
            {"aw": geo.width(), "ah": geo.height()}
            )

        cnf.write_json_cfg()
        MainUtils.close_all_win()

    def after_start(self):

        if cnf.first_load:
            from widgets.win_first_load import WinFirstLoad
            cnf.first_load = False
            Manager.first_load_win = WinFirstLoad()
            Manager.first_load_win.show()
            return

        if not MainUtils.smb_check():
            from widgets.win_smb import WinSmb

            Manager.smb_win = WinSmb()
            Manager.smb_win.show()

        utils_signals_app.scaner_start.emit()

        # self.test = TestWid()
        # self.test.show()

        # from widgets.win_smb import WinSmb
        # Manager.smb_win = WinSmb()
        # Manager.smb_win.show()


app = App()
