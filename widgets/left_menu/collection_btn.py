import os
import subprocess

from PyQt5.QtGui import QContextMenuEvent, QMouseEvent
from PyQt5.QtWidgets import QAction, QFrame, QLabel
from PyQt5.QtCore import QEvent, Qt, QTimer

from base_widgets import ContextMenuBase, ContextSubMenuBase
from cfg import cnf
from signals import gui_signals_app
from styles import Names, Themes
from utils import SendNotification, MainUtils
from ..win_smb import WinSmb

class CustomContext(ContextMenuBase):
    def __init__(self, parent: QLabel, true_name: str, event: QContextMenuEvent):
        super().__init__(event=event)

        self.my_parent = parent
        self.true_name = true_name

        view_coll = QAction(text=cnf.lng.view, parent=self)
        view_coll.triggered.connect(lambda e: self.show_collection())
        self.addAction(view_coll)

        self.addSeparator()

        action_text = f"{cnf.lng.reveal} {cnf.lng.in_finder}"
        reveal_menu = ContextSubMenuBase(parent=self, title=action_text)
        self.addMenu(reveal_menu)

        base_coll = QAction(text=cnf.lng.collection, parent=self)
        base_coll.triggered.connect(lambda e: self.reveal_collection())
        reveal_menu.addAction(base_coll)

        reveal_menu.addSeparator()

        prod_coll = QAction(text=cnf.lng.cust_fltr_names["prod"], parent=self)
        prod_coll.triggered.connect(lambda e: self.reveal_collection("prod"))
        reveal_menu.addAction(prod_coll)


        mod_coll = QAction(text=cnf.lng.cust_fltr_names["mod"], parent=self)
        mod_coll.triggered.connect(lambda e: self.reveal_collection("mod"))
        reveal_menu.addAction(mod_coll)

    def show_collection(self):
        cnf.curr_coll = self.true_name
        gui_signals_app.reload_title.emit()
        gui_signals_app.reload_menu.emit()
        gui_signals_app.reload_thumbnails.emit()

    def reveal_collection(self, flag: str = None):
        if MainUtils.smb_check():

            if self.true_name == cnf.ALL_COLLS:
                if os.path.exists(cnf.coll_folder):
                    subprocess.Popen(["open", cnf.coll_folder])
                else:
                    SendNotification(cnf.lng.no_connection)
                return

            coll_path = os.path.join(cnf.coll_folder, self.true_name)

            if flag == "prod":
                flag_path = os.path.join(coll_path, cnf.cust_fltr_names[flag])
                if os.path.exists(flag_path):
                    subprocess.Popen(["open", flag_path])
                    return

            if flag == "mod":
                flag_path = os.path.join(coll_path, cnf.cust_fltr_names[flag])
                if os.path.exists(flag_path):
                    subprocess.Popen(["open", flag_path])
                    return

            if os.path.exists(coll_path):
                subprocess.Popen(["open", coll_path])
            else:
                SendNotification(cnf.lng.no_connection)

        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()


class CollectionBtn(QLabel):
    def __init__(self, parent: QFrame, fake_name: str, true_name: str):
        super().__init__(text=fake_name)
        self.true_name = true_name
        self.fake_name = fake_name

        btn_w = cnf.MENU_W - 20 - 5
        self.setFixedSize(btn_w, 28)

        if true_name == cnf.curr_coll:
            self.setObjectName(Names.menu_btn_selected)
        else:
            self.setObjectName(Names.menu_btn)

        self.setStyleSheet(Themes.current)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.load_collection()
        return super().mouseReleaseEvent(ev)

    def load_collection(self):
        cnf.curr_coll = self.true_name
        cnf.current_photo_limit = cnf.LIMIT
        gui_signals_app.reload_title.emit()
        gui_signals_app.scroll_top.emit()
        gui_signals_app.reload_menu.emit()
        gui_signals_app.reload_thumbnails.emit()

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        try:
            self.context_menu = CustomContext(parent=self, true_name=self.true_name, event=ev)
            self.context_menu.closed.connect(self.closed_context)

            if self.objectName() == Names.menu_btn:
                self.setObjectName(Names.menu_btn_bordered)
            else:
                self.setObjectName(Names.menu_btn_selected_bordered)

            self.setStyleSheet(Themes.current)
            self.context_menu.show_menu()

            return super().contextMenuEvent(ev)

        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

    def closed_context(self):
        try:
            if self.objectName() == Names.menu_btn_bordered:
                self.setObjectName(Names.menu_btn)
            else:
                self.setObjectName(Names.menu_btn_selected)
            self.setStyleSheet(Themes.current)
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

    def enterEvent(self, a0: QEvent | None) -> None:
        if self.true_name != cnf.ALL_COLLS:
            self.setToolTip(f"{cnf.lng.collection}: {self.true_name}")
        return super().enterEvent(a0)
