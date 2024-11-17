import os
import subprocess
from collections import defaultdict

import sqlalchemy
from PyQt5.QtCore import QEvent, QObject, Qt, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QMouseEvent
from PyQt5.QtWidgets import (QAction, QFrame, QLabel, QScrollArea, QSpacerItem,
                             QWidget)

from base_widgets import ContextCustom, LayoutHor, LayoutVer
from cfg import ALL_COLLS, FAVS, LIMIT, MENU_W, Dynamic, JsonData
from database import THUMBS, Dbase
from signals import SignalsApp
from styles import Names, Themes
from utils.utils import QThreadPool, URunnable, Utils

from .win_smb import WinSmb


class CustomContext(ContextCustom):
    def __init__(self, parent: QLabel, true_name: str, event: QContextMenuEvent):
        super().__init__(event=event)

        self.my_parent = parent
        self.true_name = true_name

        view_coll = QAction(text=Dynamic.lng.view, parent=self)
        view_coll.triggered.connect(lambda e: self.show_collection())
        self.addAction(view_coll)

        t = Dynamic.lng.detail_menu if JsonData.small_menu_view else Dynamic.lng.compact_menu
        view = QAction(text=t, parent=self)
        view.triggered.connect(lambda e: self.change_view())
        self.addAction(view)

        self.addSeparator()

        reveal_coll = QAction(text=Dynamic.lng.reveal_in_finder, parent=self)
        reveal_coll.triggered.connect(self.reveal_collection)
        self.addAction(reveal_coll)

    def change_view(self):
        JsonData.small_menu_view = not JsonData.small_menu_view
        SignalsApp.all_.reload_menu_left.emit()

    def show_collection(self):
        JsonData.curr_coll = self.true_name
        SignalsApp.all_.win_main_cmd.emit("set_title")
        SignalsApp.all_.reload_menu_left.emit()
        SignalsApp.all_.grid_thumbnails_cmd.emit("to_top")
        SignalsApp.all_.grid_thumbnails_cmd.emit("reload")

    def reveal_collection(self):
        if self.true_name == ALL_COLLS:
            coll = JsonData.coll_folder
        else:
            coll = os.path.join(JsonData.coll_folder, self.true_name)

        if Utils.smb_check():
            if os.path.exists(coll):
                subprocess.Popen(["open", coll])
                return
        else:
            self.smb_win = WinSmb()
            self.smb_win.center_relative_parent(self.my_parent)
            self.smb_win.show()


class CollectionBtn(QLabel):
    def __init__(self, parent: QFrame, fake_name: str, true_name: str):
        super().__init__(text=fake_name)
        self.true_name = true_name
        self.fake_name = fake_name

        btn_w = MENU_W - 20 - 5
        self.setFixedSize(btn_w, 28)

        if true_name == JsonData.curr_coll:
            self.setObjectName(Names.menu_btn_selected)
        else:
            self.setObjectName(Names.menu_btn)

        self.setStyleSheet(Themes.current)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            JsonData.curr_coll = self.true_name
            Dynamic.current_photo_limit = LIMIT
            SignalsApp.all_.win_main_cmd.emit("set_title")
            SignalsApp.all_.reload_menu_left.emit()
            SignalsApp.all_.grid_thumbnails_cmd.emit("reload")
            SignalsApp.all_.grid_thumbnails_cmd.emit("to_top")

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

        except Exception as e:
            Utils.print_err(error=e)

    def closed_context(self):
        try:
            if self.objectName() == Names.menu_btn_bordered:
                self.setObjectName(Names.menu_btn)
            else:
                self.setObjectName(Names.menu_btn_selected)
            self.setStyleSheet(Themes.current)

        except Exception as e:
            Utils.print_err(error=e)


class BaseLeftMenu(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setObjectName(Names.menu_scrollbar)
        self.setStyleSheet(Themes.current)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.init_ui()
        SignalsApp.all_.reload_menu_left.connect(self.reload_menu)

    def init_ui(self):
        if hasattr(self, "main_wid"):
            self.main_wid.deleteLater()

        self.main_wid = QWidget()
        self.main_wid.setObjectName(Names.menu_scrollbar_qwidget)
        self.main_wid.setStyleSheet(Themes.current)
        self.setWidget(self.main_wid)

        self.main_layout = LayoutVer()
        self.main_wid.setLayout(self.main_layout)

        btns_widget = QWidget()
        main_btns_layout = LayoutVer()
        btns_widget.setLayout(main_btns_layout)

        main_btns_layout.setContentsMargins(0, 5, 0, 15)

        label = CollectionBtn(parent=self, fake_name=Dynamic.lng.all_colls,
                              true_name=ALL_COLLS)
        main_btns_layout.addWidget(label)

        label = CollectionBtn(parent=self, fake_name=Dynamic.lng.fav_coll,
                              true_name=FAVS)
        main_btns_layout.addWidget(label)

        self.main_layout.addWidget(btns_widget)

        if JsonData.small_menu_view:
            for letter, collections in self.load_colls_query().items():
                for coll in collections:
                    label = CollectionBtn(
                        parent=self,
                        fake_name=coll["fake_name"],
                        true_name=coll["true_name"]
                        )
                    self.main_layout.addWidget(label)
        else:
            for letter, collections in self.load_colls_query().items():

                test = QLabel(text=letter)
                test.setContentsMargins(6, 20, 0, 5)
                test.setObjectName(Names.letter_btn)
                test.setStyleSheet(Themes.current)
                self.main_layout.addWidget(test)

                for coll in collections:
                    label = CollectionBtn(
                        parent=self,
                        fake_name=coll["fake_name"],
                        true_name=coll["true_name"]
                        )
                    self.main_layout.addWidget(label)

        self.main_layout.addSpacerItem(QSpacerItem(0, 5))
        self.main_layout.addStretch(1)

    def change_view(self):
        JsonData.small_menu_view = not JsonData.small_menu_view
        SignalsApp.all_.reload_menu_left.emit()

    def load_colls_query(self) -> dict:
        menus = defaultdict(list)

        conn = Dbase.engine.connect()
        q = sqlalchemy.select(THUMBS.c.coll).distinct()
        res = conn.execute(q).fetchall()
        conn.close()

        if res:
            res = (i[0] for i in res if i)
        else:
            print("widgets > left menu > load db colls > row is empty")
            return menus

        for true_name in res:
            fake_name = true_name.lstrip("0123456789").strip()
            fake_name = fake_name if fake_name else true_name
            letter = fake_name[0].capitalize()

            menus[letter].append({"fake_name": fake_name, "true_name": true_name})

        return {
            key: sorted(value, key=lambda x: x['fake_name'])
            for key, value in sorted(menus.items())
            }

    def reload_menu(self):
        self.init_ui()


class MenuLeft(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(MENU_W)

        h_lay = LayoutHor()
        self.setLayout(h_lay)

        fake = QFrame()
        fake.setFixedWidth(10)
        fake.setObjectName("menu_fake_widget")
        fake.setStyleSheet(Themes.current)
        h_lay.addWidget(fake)

        menu = BaseLeftMenu()
        h_lay.addWidget(menu)
