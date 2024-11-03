from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QKeyEvent, QResizeEvent
from PyQt5.QtWidgets import QDesktopWidget, QFrame, QPushButton, QVBoxLayout

from base_widgets import LayoutH, LayoutV, WinBase
from cfg import ALL_COLLS, APP_NAME, Dynamic, JsonData
from signals import SignalsApp
from styles import Names, Themes
from utils.main_utils import MainUtils
from utils.scaner import ScanerShedule

from .bar_bottom import BarBottom
from .bar_macos import BarMacos
from .bar_top import BarTop
from .grid.main import Thumbnails
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


class RightWidget(QFrame):
    def __init__(self):
        super().__init__()
        v_layout = LayoutV()
        self.setLayout(v_layout)

        self.filters_bar = BarTop()
        v_layout.addWidget(self.filters_bar)

        self.thumbnails = Thumbnails()
        v_layout.addWidget(self.thumbnails)

        self.st_bar = BarBottom()
        v_layout.addWidget(self.st_bar)

        self.notification = Notification(parent=self)
        self.notification.move(2, 2)
        self.notification.hide()

        SignalsApp.all.noti_win_main.connect(self.notification.show_notify)
        
    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        w, h = self.thumbnails.width() - 6, self.filters_bar.height() - 5
        self.notification.resize(w, h)
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
        self.set_title(self.get_coll())

        menubar = BarMacos()
        self.setMenuBar(menubar)

        search_bar = WidSearch()
        self.titlebar.add_r_wid(search_bar)

        content_wid = ContentWid()
        self.central_layout.addWidget(content_wid)

        SignalsApp.all.win_main_cmd.connect(self.win_main_cmd)
        QTimer.singleShot(100, self.after_start)

    def win_main_cmd(self, flag: str):
        if flag == "show":
            self.show()
        elif flag == "exit":
            self.on_exit()
        elif flag == "set_title":
            self.set_title(self.get_coll())
        else: 
            raise Exception("app > win main > wrong flag", flag)

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

    def on_exit(self):
        SignalsApp.all.scaner_toggle.emit("stop")
        geo = self.geometry()
        JsonData.root_g.update({"aw": geo.width(), "ah": geo.height()})
        JsonData.write_json_data()

    def after_start(self):
        if not MainUtils.smb_check():
            self.smb_win = WinSmb(parent=self.main_win)
            self.smb_win.show()
        else:
            self.scaner = ScanerShedule()
            SignalsApp.all.scaner_toggle.emit("start")

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
