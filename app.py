import os
import sys

from PyQt5.QtCore import QEvent, QObject, Qt, QTimer
from PyQt5.QtGui import (QCloseEvent, QDragEnterEvent, QDragLeaveEvent,
                         QDropEvent, QIcon, QKeyEvent, QResizeEvent)
from PyQt5.QtWidgets import (QAction, QApplication, QDesktopWidget,
                             QFileDialog, QFrame, QLabel, QPushButton,
                             QVBoxLayout)

from base_widgets import LayoutH, LayoutV, WinBase
from cfg import ALL_COLLS, APP_NAME, Dynamic, JsonData
from signals import signals_app
from styles import Names, Themes
from utils.copy_files import ThreadCopyFiles
from utils.main_utils import MainUtils
from utils.scaner import ScanerShedule
from widgets import (BarBottom, BarMacos, BarTop, MenuLeft, Notification,
                     Thumbnails, WidSearch)
from widgets.win_smb import WinSmb


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


class RightWidget(QFrame):
    def __init__(self):
        super().__init__()

        v_layout = LayoutV(self)

        self.filters_bar = BarTop()
        self.thumbnails = Thumbnails()
        self.st_bar = BarBottom()

        v_layout.addWidget(self.filters_bar)
        v_layout.addWidget(self.thumbnails)
        v_layout.addWidget(self.st_bar)

        self.notification = Notification(parent=self)
        signals_app.noti_win_main.connect(self.notification.show_notify)
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

        self.left_menu = MenuLeft()
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setObjectName(Names.separator)
        sep.setStyleSheet(Themes.current)
        self.right_widget = RightWidget()

        h_layout.addWidget(self.left_menu)
        h_layout.addWidget(sep)
        h_layout.addWidget(self.right_widget)


class WinMain(WinBase):
    def __init__(self):
        super().__init__(close_func=self.my_close_event)

        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle(APP_NAME)
        self.resize(JsonData.root_g["aw"], JsonData.root_g["ah"])
        self.center()

        menubar = BarMacos()
        self.setMenuBar(menubar)

        search_bar = WidSearch()
        self.titlebar.add_r_wid(search_bar)

        self.set_title(self.get_coll())
        signals_app.reload_win_main_title.connect(lambda: self.set_title(self.get_coll()))

        content_wid = ContentWid()
        self.central_layout.addWidget(content_wid)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)

        QTimer.singleShot(100, self.after_start)
        self.installEventFilter(self)

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def get_coll(self) -> str:
        if JsonData.curr_coll == ALL_COLLS:
            return Dynamic.lng.all_colls
        else:
            return JsonData.curr_coll
    
    def my_close_event(self, a0: QCloseEvent | None) -> None:
        self.titlebar.btns.nonfocused_icons()
        self.hide()
        a0.ignore()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_W:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.my_close_event(a0)

        elif a0.key() == Qt.Key.Key_F:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                signals_app.search_wid_focus.emit()

        elif a0.key() == Qt.Key.Key_Escape:
            a0.ignore()

        elif a0.key() == Qt.Key.Key_Equal:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if JsonData.curr_size_ind < 3:
                    JsonData.curr_size_ind += 1
                    signals_app.slider_change_value.emit(JsonData.curr_size_ind)

        elif a0.key() == Qt.Key.Key_Minus:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if JsonData.curr_size_ind > 0:
                    JsonData.curr_size_ind -= 1
                    signals_app.slider_change_value.emit(JsonData.curr_size_ind)

        elif a0.key() == Qt.Key.Key_Q:
            self.on_exit()

    def on_exit(self):
        signals_app.scaner_toggle.emit("stop")
        geo = self.geometry()
        JsonData.root_g.update({"aw": geo.width(), "ah": geo.height()})
        JsonData.write_config()
        # QApplication.quit()

    def after_start(self):
        if not MainUtils.smb_check():
            from widgets.win_smb import WinSmb

            self.smb_win = WinSmb(parent=self.main_win)
            self.smb_win.show()

        else:
            self.scaner = ScanerShedule()
            signals_app.scaner_toggle.emit("start")


class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        if os.path.basename(os.path.dirname(__file__)) != "Resources":
            self.setWindowIcon(QIcon(os.path.join("icon", "icon.icns")))

        self.installEventFilter(self)
        # self.aboutToQuit.connect(self.on_exit)

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a1.type() == QEvent.Type.ApplicationActivate:
            ...
            # if self.main_win.isMinimized() or self.main_win.isHidden():
            #     self.main_win.show()
            # if Dynamic.image_viewer:
            #     if Dynamic.image_viewer.isMinimized() or Dynamic.image_viewer.isHidden():
            #             Dynamic.image_viewer.show()
            #             Dynamic.image_viewer.showNormal()

        return super().eventFilter(a0, a1)
    

        # self.test = TestWid()
        # self.test.setWindowModality(Qt.WindowModality.ApplicationModal)
        # self.test.show()
        

Themes.set_theme(JsonData.theme)
