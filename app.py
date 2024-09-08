import os
import sys

from PyQt5.QtCore import QEvent, QObject, Qt, QTimer
from PyQt5.QtGui import (QDragEnterEvent, QDragLeaveEvent, QDropEvent, QIcon,
                         QKeyEvent, QResizeEvent)
from PyQt5.QtWidgets import (QAction, QApplication, QDesktopWidget,
                             QFileDialog, QFrame, QLabel, QPushButton,
                             QVBoxLayout, QWidget)

from base_widgets import LayoutH, LayoutV, WinBase
from cfg import cnf
from signals import gui_signals_app, utils_signals_app
from styles import Names, Themes
from utils import MainUtils
from utils.copy_files import ThreadCopyFiles
from utils.reveal_files import RevealFiles
from utils.send_notification import SendNotification
from widgets import (FiltersBar, LeftMenu, MacMenuBar, Notification, SearchBar,
                     StBar, Thumbnails)
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
        from widgets.win_downloads import DownloadsWin
        win = DownloadsWin(parent=self)
        win.center_win(parent=self)
        win.show()


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
        # Themes.set_theme("dark_theme")
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

        self.drop_widget = QLabel(parent=self.centralWidget(), text=cnf.lng.drop_to_collections)
        self.drop_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_widget.setObjectName(Names.drop_widget)
        self.drop_widget.setStyleSheet(Themes.current)
        self.drop_widget.hide()

        # что делать при выходе
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)

        self.setAcceptDrops(True)

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def mycloseEvent(self, event):
        self.titlebar.btns.nonfocused_icons()
        self.hide()
        event.ignore()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_W:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.mycloseEvent(a0)

        elif a0.key() == Qt.Key.Key_F:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                gui_signals_app.set_focus_search.emit()

        elif a0.key() == Qt.Key.Key_Escape:
            a0.ignore()

        # return super().keyPressEvent(a0)

    def reload_title(self):
        self.set_title(self.check_coll())

    def check_coll(self) -> str:
        if cnf.curr_coll == cnf.ALL_COLLS:
            return cnf.lng.all_colls
        else:
            return cnf.curr_coll

    def dragEnterEvent(self, a0: QDragEnterEvent | None) -> None:
        if not a0.source() and a0.mimeData().hasUrls():
            self.drop_widget.resize(self.width(), self.height())
            self.drop_widget.show()
            a0.acceptProposedAction()
        return super().dragEnterEvent(a0)

    def dropEvent(self, a0: QDropEvent | None) -> None:
        if a0.mimeData().hasUrls():
            files = [url.toLocalFile() for url in a0.mimeData().urls()]
            self.drop_widget.hide()

            if not MainUtils.smb_check():
                self.win_smb = WinSmb(parent=self)
                self.win_smb.show()
                return

            directory = cnf.coll_folder
            if cnf.curr_coll != cnf.ALL_COLLS:
                directory = os.path.join(cnf.coll_folder, cnf.curr_coll)


            folder = QFileDialog.getExistingDirectory(self, directory=directory)

            if folder:
                self.copy_task = ThreadCopyFiles(dest=folder, files=files)
                self.copy_task.finished.connect(lambda files: self.copy_files_fin(self.copy_task, files))
                gui_signals_app.show_downloads.emit()
                self.copy_task.start()
            
            a0.acceptProposedAction()

        return super().dropEvent(a0)
    
    def copy_files_fin(self, copy_task: ThreadCopyFiles, files: list):
        self.reveal_files = RevealFiles(files)
        if len(cnf.copy_threads) == 0:
            gui_signals_app.hide_downloads.emit()
        try:
            copy_task.remove_threads()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)
    
    def dragLeaveEvent(self, a0: QDragLeaveEvent | None) -> None:
        self.drop_widget.hide()
        return super().dragLeaveEvent(a0)
        

class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        if os.path.basename(os.path.dirname(__file__)) != "Resources":
            self.setWindowIcon(QIcon(os.path.join("icon", "icon.icns")))

        self.main_win = WinMain()
        self.main_win.show()

        self.installEventFilter(self)
        self.aboutToQuit.connect(self.on_exit)

        QTimer.singleShot(100, self.after_start)

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a1.type() == QEvent.Type.ApplicationActivate:
            if self.main_win.isMinimized() or self.main_win.isHidden():
                self.main_win.show()
            if cnf.image_viewer:
                if cnf.image_viewer.isMinimized() or cnf.image_viewer.isHidden():
                        cnf.image_viewer.show()
                        cnf.image_viewer.showNormal()

        return super().eventFilter(a0, a1)
    
    def on_exit(self):
        utils_signals_app.scaner_stop.emit()

        geo = self.main_win.geometry()

        cnf.root_g.update(
            {"aw": geo.width(), "ah": geo.height()}
            )

        cnf.write_json_cfg()

    def after_start(self):

        if not MainUtils.smb_check():
            from widgets.win_smb import WinSmb

            self.smb_win = WinSmb(parent=self.main_win)
            self.smb_win.show()

        utils_signals_app.scaner_start.emit()
        

Themes.set_theme(cnf.theme)
app = App()