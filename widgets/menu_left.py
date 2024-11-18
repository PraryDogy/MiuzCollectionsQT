import os
import subprocess

import sqlalchemy
from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QMouseEvent
from PyQt5.QtWidgets import (QAction, QFrame, QLabel, QScrollArea, QSpacerItem,
                             QWidget)

from base_widgets import ContextCustom, LayoutHor, LayoutVer
from cfg import MENU_LEFT_WIDTH, NAME_ALL_COLLS, NAME_FAVS, Dynamic, JsonData
from database import THUMBS, Dbase
from signals import SignalsApp
from styles import Names, Themes
from utils.utils import URunnable, UThreadPool, Utils

from .win_smb import WinSmb


class CollectionBtn(QLabel):
    pressed_ = pyqtSignal()

    def __init__(self, fake_name: str, true_name: str):
        super().__init__(text=fake_name)
        self.true_name = true_name
        self.fake_name = fake_name

        btn_w = MENU_LEFT_WIDTH - 20 - 5
        self.setFixedSize(btn_w, 28)

    def reveal_collection(self, *args):

        if self.true_name in (NAME_ALL_COLLS, NAME_FAVS):
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

    def normal_style(self):
        self.setObjectName(Names.menu_btn)
        self.setStyleSheet(Themes.current)

    def selected_style(self):
        self.setObjectName(Names.menu_btn_selected)
        self.setStyleSheet(Themes.current)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.pressed_.emit()

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:

        menu_ = ContextCustom(event=ev)

        view_coll = QAction(text=Dynamic.lang.view, parent=self)
        view_coll.triggered.connect(self.pressed_.emit)
        menu_.addAction(view_coll)

        menu_.addSeparator()

        reveal_coll = QAction(text=Dynamic.lang.reveal_in_finder, parent=self)
        reveal_coll.triggered.connect(self.reveal_collection)
        menu_.addAction(reveal_coll)

        if self.objectName() == Names.menu_btn:
            self.setObjectName(Names.menu_btn_bordered)
        else:
            self.setObjectName(Names.menu_btn_selected_bordered)

        self.setStyleSheet(Themes.current)

        menu_.show_menu()

        if self.objectName() == Names.menu_btn_bordered:
            self.setObjectName(Names.menu_btn)
        else:
            self.setObjectName(Names.menu_btn_selected)
        self.setStyleSheet(Themes.current)


class WorkerSignals(QObject):
    finished_ = pyqtSignal(list)


class LoadMenus(URunnable):
    def __init__(self):
        super().__init__()
        self.signals_ = WorkerSignals()

    @URunnable.set_running_state
    def run(self):
        menus = self.load_colls_query()
        self.signals_.finished_.emit(menus)

    def load_colls_query(self) -> list[dict]:
        menus: list[dict] = []

        conn = Dbase.engine.connect()
        q = sqlalchemy.select(THUMBS.c.coll).distinct()
        res = conn.execute(q).fetchall()
        conn.close()

        if res:
            res: tuple[str] = (i[0] for i in res if i)

        else:
            print("widgets > left menu > load db colls > row is empty")
            return menus

        for true_name in res:
            fake_name = true_name.lstrip("0123456789").strip()
            fake_name = fake_name if fake_name else true_name

            menus.append(
                {
                    "fake_name": fake_name,
                    "true_name": true_name
                }
            )

        return sorted(menus, key = lambda x: x["fake_name"])


class BaseLeftMenu(QScrollArea):
    coll_btn: CollectionBtn

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setObjectName(Names.menu_scrollbar)
        self.setStyleSheet(Themes.current)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setup_task()
        SignalsApp.all_.reload_menu_left.connect(self.setup_task)

    def setup_task(self):
        self.task_ = LoadMenus()
        self.task_.signals_.finished_.connect(self.task_finalize)
        UThreadPool.pool.start(self.task_)

    def collection_btn_cmd(self, btn: CollectionBtn):
        JsonData.curr_coll = btn.true_name
        Dynamic.grid_offset = 0
        SignalsApp.all_.win_main_cmd.emit("set_title")
        SignalsApp.all_.grid_thumbnails_cmd.emit("reload")
        SignalsApp.all_.grid_thumbnails_cmd.emit("to_top")

        BaseLeftMenu.coll_btn.normal_style()
        btn.selected_style()
        BaseLeftMenu.coll_btn = btn

    def task_finalize(self, menus: list[dict[str, str]]):

        if hasattr(self, "main_wid"):
            self.main_wid.deleteLater()

        self.main_wid = QWidget()
        self.main_wid.setObjectName(Names.menu_scrollbar_qwidget)
        self.main_wid.setStyleSheet(Themes.current)
        self.setWidget(self.main_wid)

        main_layout = LayoutVer()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_wid.setLayout(main_layout)

        btns_widget = QWidget()
        main_layout.addWidget(btns_widget)

        main_btns_layout = LayoutVer()
        btns_widget.setLayout(main_btns_layout)

        main_btns_layout.setContentsMargins(0, 5, 0, 15)

        all_colls_btn = CollectionBtn(
            fake_name=Dynamic.lang.all_colls,
            true_name=NAME_ALL_COLLS
            )
        cmd_ = lambda: self.collection_btn_cmd(all_colls_btn)
        all_colls_btn.pressed_.connect(cmd_)
        main_btns_layout.addWidget(all_colls_btn)

        favs_btn = CollectionBtn(
            fake_name=Dynamic.lang.fav_coll,
            true_name=NAME_FAVS
            )
        cmd_ = lambda: self.collection_btn_cmd(favs_btn)
        favs_btn.pressed_.connect(cmd_)
        main_btns_layout.addWidget(favs_btn)

        for i in (all_colls_btn, favs_btn):
            if i.true_name == JsonData.curr_coll:
                i.selected_style()
                BaseLeftMenu.coll_btn = i

        for data in menus:

            coll_btn = CollectionBtn(
                fake_name=data.get("fake_name"),
                true_name=data.get("true_name")
                )
            cmd_ = lambda wid=coll_btn: self.collection_btn_cmd(wid)
            coll_btn.pressed_.connect(cmd_)
            main_layout.addWidget(coll_btn)

            if coll_btn.true_name == JsonData.curr_coll:
                coll_btn.selected_style()
                BaseLeftMenu.coll_btn = coll_btn

        main_layout.addSpacerItem(QSpacerItem(0, 5))


class MenuLeft(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(MENU_LEFT_WIDTH)

        h_lay = LayoutHor()
        self.setLayout(h_lay)

        fake = QFrame()
        fake.setFixedWidth(10)
        fake.setObjectName("menu_fake_widget")
        fake.setStyleSheet(Themes.current)
        h_lay.addWidget(fake)

        menu = BaseLeftMenu()
        h_lay.addWidget(menu)
