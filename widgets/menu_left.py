import os
import subprocess
from collections import defaultdict

import sqlalchemy
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QContextMenuEvent, QMouseEvent
from PyQt5.QtWidgets import (QAction, QFrame, QLabel, QScrollArea, QSpacerItem,
                             QWidget)

from base_widgets import ContextMenuBase, ContextSubMenuBase, LayoutH, LayoutV
from cfg import cnf
from database import Dbase, ThumbsMd
from signals import signals_app
from styles import Names, Themes
from utils.main_utils import MainUtils

from .win_smb import WinSmb


class CustomContext(ContextMenuBase):
    def __init__(self, parent: QLabel, true_name: str, event: QContextMenuEvent):
        super().__init__(event=event)

        self.my_parent = parent
        self.true_name = true_name

        view_coll = QAction(text=cnf.lng.view, parent=self)
        view_coll.triggered.connect(lambda e: self.show_collection())
        self.addAction(view_coll)

        t = cnf.lng.detail_menu if cnf.small_menu_view else cnf.lng.compact_menu
        view = QAction(text=t, parent=self)
        view.triggered.connect(lambda e: self.change_view())
        self.addAction(view)

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

    def change_view(self):
        cnf.small_menu_view = not cnf.small_menu_view
        signals_app.reload_menu.emit()

    def show_collection(self):
        cnf.curr_coll = self.true_name
        signals_app.reload_title.emit()
        signals_app.reload_menu.emit()
        signals_app.reload_thumbnails.emit()

    def reveal_collection(self, flag: str = None):
        if MainUtils.smb_check():

            if self.true_name == cnf.ALL_COLLS:
                if os.path.exists(cnf.coll_folder):
                    subprocess.Popen(["open", cnf.coll_folder])
                    return

            coll_path = os.path.join(cnf.coll_folder, self.true_name)

            if flag == "prod":
                flag_path = os.path.join(coll_path, cnf.cust_fltr_names[flag])
                if os.path.exists(flag_path):
                    subprocess.Popen(["open", flag_path])
                    return
                else:
                    os.mkdir(flag_path)
                    subprocess.Popen(["open", flag_path])
                    return

            if flag == "mod":
                flag_path = os.path.join(coll_path, cnf.cust_fltr_names[flag])
                if os.path.exists(flag_path):
                    subprocess.Popen(["open", flag_path])
                    return
                else:
                    os.mkdir(flag_path)
                    subprocess.Popen(["open", flag_path])
                    return

            if os.path.exists(coll_path):
                subprocess.Popen(["open", coll_path])
                return

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
        signals_app.reload_title.emit()
        signals_app.scroll_top.emit()
        signals_app.reload_menu.emit()
        signals_app.reload_thumbnails.emit()

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


class BaseLeftMenu(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setObjectName(Names.menu_scrollbar)
        self.setStyleSheet(Themes.current)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        scroll_widget.setObjectName(Names.menu_scrollbar_qwidget)
        scroll_widget.setStyleSheet(Themes.current)
        self.setWidget(scroll_widget)

        self.v_layout = LayoutV()
        scroll_widget.setLayout(self.v_layout)
        self.init_ui()
        signals_app.reload_menu.connect(self.reload_menu)

    def init_ui(self):
        btns_widget = QWidget()
        main_btns_layout = LayoutV()
        btns_widget.setLayout(main_btns_layout)

        main_btns_layout.setContentsMargins(0, 5, 0, 15)

        label = CollectionBtn(parent=self, fake_name=cnf.lng.all_colls,
                              true_name=cnf.ALL_COLLS)
        main_btns_layout.addWidget(label)

        self.v_layout.addWidget(btns_widget)

        if cnf.small_menu_view:
            for letter, collections in self.load_colls_query().items():
                for coll in collections:
                    label = CollectionBtn(parent=self, fake_name=coll["fake_name"], true_name=coll["true_name"])
                    self.v_layout.addWidget(label)
        else:
            for letter, collections in self.load_colls_query().items():

                test = QLabel(text=letter)
                test.setContentsMargins(6, 20, 0, 5)
                test.setObjectName(Names.letter_btn)
                test.setStyleSheet(Themes.current)
                self.v_layout.addWidget(test)

                for coll in collections:
                    label = CollectionBtn(parent=self, fake_name=coll["fake_name"], true_name=coll["true_name"])
                    self.v_layout.addWidget(label)

        self.v_layout.addSpacerItem(QSpacerItem(0, 5))
        self.v_layout.addStretch(1)

    def change_view(self):
        cnf.small_menu_view = not cnf.small_menu_view
        signals_app.reload_menu.emit()

    def load_colls_query(self) -> dict:
        menus = defaultdict(list)
        
        q = sqlalchemy.select(ThumbsMd.collection).distinct()
        conn = Dbase.engine.connect()
        try:
            res = (i[0] for i in conn.execute(q).fetchall() if i)
        finally:
            conn.close()

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
        MainUtils.clear_layout(self.v_layout)
        self.init_ui()


class MenuLeft(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(cnf.MENU_W)

        h_lay = LayoutH()
        self.setLayout(h_lay)

        fake = QFrame()
        fake.setFixedWidth(10)
        fake.setObjectName("menu_fake_widget")
        fake.setStyleSheet(Themes.current)
        h_lay.addWidget(fake)

        menu = BaseLeftMenu()
        h_lay.addWidget(menu)
