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

    def __init__(self, short_name: str, coll_name: str):
        """
        Initializes the CollectionBtn widget.

        :param short_name: The short version of the collection name, stripped of initial digits and symbols.
        :param coll_name: The full name of the collection.
        """

        super().__init__(text=short_name)
        self.coll_name = coll_name
        self.short_name = short_name

        btn_w = MENU_LEFT_WIDTH - 20 - 5
        self.setFixedSize(btn_w, 28)

    def reveal_collection(self, *args) -> None:
        """
        Opens the collection folder if it exists and SMB check passes, 
        otherwise shows an SMB connection window.

        :param args: Additional arguments (unused).
        :return: None
        """

        if self.coll_name in (NAME_ALL_COLLS, NAME_FAVS):
            coll = JsonData.coll_folder
        else:
            coll = os.path.join(JsonData.coll_folder, self.coll_name)

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
    def run(self) -> None:
        """
        Main execution method for the `LoadMenus` class. This method is part of `URunnable`, 
        which inherits from `QRunnable`, and should be executed using `UThreadPool.pool.start`.
        
        `UThreadPool` is a subclass of `QThreadPool` that manages the execution of runnable objects.
        
        Loads collection data and emits the `finished_` signal with the result.
        """
        menus = self.load_colls_query()
        self.signals_.finished_.emit(menus)


    def load_colls_query(self) -> list[dict]:
        """
        Queries the database to load distinct `THUMBS.c.coll`, processes them, 
        and returns a list of dictionaries containing short and full `THUMBS.c.coll`.

        :return: A sorted list of dictionaries with `short_name` and `coll_name` keys.
        """
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

        for coll_name in res:
            fake_name = coll_name.lstrip("0123456789").strip()
            fake_name = fake_name if fake_name else coll_name

            menus.append(
                {
                    "short_name": fake_name,
                    "coll_name": coll_name
                }
            )

        return sorted(menus, key = lambda x: x["short_name"])


class MenuLeft(QFrame):
    coll_btn: CollectionBtn

    def __init__(self):
        super().__init__()
        self.setFixedWidth(MENU_LEFT_WIDTH)
        self.setObjectName("menu_fake_widget")
        self.setStyleSheet(Themes.current)

        scroll_layout = LayoutVer()
        scroll_layout.setContentsMargins(5, 0, 0, 5)
        self.setLayout(scroll_layout)

        self.selected_btn: CollectionBtn
        SignalsApp.all_.menu_left_cmd.connect(self.menu_left_cmd)

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName(Names.menu_scrollbar)
        self.scroll_area.setStyleSheet(Themes.current)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_layout.addWidget(self.scroll_area)

        self.setup_task()

    def menu_left_cmd(self, flag: str):
        """
        Handles the signal `SignalsApp.all_.menu_left_cmd` with a flag.
        
        :param flag: Allowed values are "one" and "two".
        """

        if flag == "reload":
            self.setup_task()

        elif flag == "select_all_colls":
            self.selected_btn.normal_style()
            self.all_colls_btn.selected_style()
            self.selected_btn = self.all_colls_btn

        else:
            raise Exception("widgets > menu left > wrong flag", flag)

    def setup_task(self):
        self.task_ = LoadMenus()
        self.task_.signals_.finished_.connect(self.init_ui)
        UThreadPool.pool.start(self.task_)

    def collection_btn_cmd(self, btn: CollectionBtn):
        """
        This is a command for `CollectionBtn`. It sets `curr_coll` based
        on the button's `coll_name`, 
        resets `grid_offset`, sets the window title, and reloads the image
        grid according to the `curr_coll`.

        :param btn: An instance of `CollectionBtn` representing the button
        that was pressed.
        """

        JsonData.curr_coll = btn.coll_name
        Dynamic.grid_offset = 0
        SignalsApp.all_.win_main_cmd.emit("set_title")
        SignalsApp.all_.grid_thumbnails_cmd.emit("reload")
        SignalsApp.all_.grid_thumbnails_cmd.emit("to_top")

        self.selected_btn.normal_style()
        btn.selected_style()
        self.selected_btn = btn

    def init_ui(self, menus: list[dict[str, str]]):

        if hasattr(self, "main_wid"):
            self.main_wid.deleteLater()

        self.main_wid = QWidget()
        self.main_wid.setObjectName(Names.menu_scrollbar_qwidget)
        self.main_wid.setStyleSheet(Themes.current)
        self.scroll_area.setWidget(self.main_wid)

        main_layout = LayoutVer()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_wid.setLayout(main_layout)

        btns_widget = QWidget()
        main_layout.addWidget(btns_widget)

        main_btns_layout = LayoutVer()
        btns_widget.setLayout(main_btns_layout)

        self.all_colls_btn = CollectionBtn(
            short_name=Dynamic.lang.all_colls,
            coll_name=NAME_ALL_COLLS
            )
        cmd_ = lambda: self.collection_btn_cmd(self.all_colls_btn)
        self.all_colls_btn.pressed_.connect(cmd_)
        main_btns_layout.addWidget(self.all_colls_btn)

        favs_btn = CollectionBtn(
            short_name=Dynamic.lang.fav_coll,
            coll_name=NAME_FAVS
            )
        cmd_ = lambda: self.collection_btn_cmd(favs_btn)
        favs_btn.pressed_.connect(cmd_)
        main_btns_layout.addWidget(favs_btn)

        for i in (self.all_colls_btn, favs_btn):
            if i.coll_name == JsonData.curr_coll:
                i.selected_style()
                self.selected_btn = i
            else:
                i.normal_style()

        for data in menus:

            coll_btn = CollectionBtn(
                short_name=data.get("short_name"),
                coll_name=data.get("coll_name")
                )
            cmd_ = lambda wid=coll_btn: self.collection_btn_cmd(wid)
            coll_btn.pressed_.connect(cmd_)
            main_layout.addWidget(coll_btn)

            if coll_btn.coll_name == JsonData.curr_coll:
                coll_btn.selected_style()
                self.selected_btn = coll_btn
            else:
                coll_btn.normal_style()

        main_layout.addSpacerItem(QSpacerItem(0, 5))
