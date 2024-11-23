import os
import subprocess

import sqlalchemy
from PyQt5.QtCore import QObject, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QMouseEvent
from PyQt5.QtWidgets import (QAction, QLabel, QListWidget, QListWidgetItem,
                             QScrollArea, QSpacerItem)

from base_widgets import ContextCustom, LayoutVer
from cfg import MENU_LEFT_WIDTH, NAME_ALL_COLLS, NAME_FAVS, Dynamic, JsonData
from database import THUMBS, Dbase
from lang import Lang
from signals import SignalsApp
from utils.utils import URunnable, UThreadPool, Utils

from .actions import OpenWins


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
            OpenWins.smb(self.window())

    def style_normal(self):
        ...

    def style_solid(self):
        ...

    def style_border(self):
        ...

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.pressed_.emit()

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:

        menu_ = ContextCustom(event=ev)

        view_coll = QAction(text=Lang.view, parent=self)
        view_coll.triggered.connect(self.pressed_.emit)
        menu_.addAction(view_coll)

        menu_.addSeparator()

        reveal_coll = QAction(text=Lang.reveal_in_finder, parent=self)
        reveal_coll.triggered.connect(self.reveal_collection)
        menu_.addAction(reveal_coll)

        menu_.show_menu()

        if JsonData.curr_coll == self.coll_name:
            ...
        else:
            ...


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


class MenuLeft(QListWidget):
    h_ = 30

    def __init__(self):
        super().__init__()
        self.setFixedWidth(MENU_LEFT_WIDTH)

        self.selected_btn: CollectionBtn
        SignalsApp.all_.menu_left_cmd.connect(self.menu_left_cmd)

        self.setup_task()

    def menu_left_cmd(self, flag: str):
        """
        Handles the signal `SignalsApp.all_.menu_left_cmd` with a flag.
        
        :param flag: Allowed values are "one" and "two".
        """

        if flag == "reload":
            self.setup_task()

        elif flag == "select_all_colls":
            ...
            print("select_all_colls")
            # self.selected_btn.style_normal()
            # self.all_colls_btn.style_solid()
            # self.selected_btn = self.all_colls_btn

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

        # self.selected_btn.style_normal()
        # btn.style_solid()
        self.selected_btn = btn

    def init_ui(self, menus: list[dict[str, str]]):

        "удалить все виджеты"

        self.all_colls_btn = CollectionBtn(
            short_name=Lang.all_colls,
            coll_name=NAME_ALL_COLLS
            )
        cmd_ = lambda: self.collection_btn_cmd(self.all_colls_btn)
        self.all_colls_btn.pressed_.connect(cmd_)

        list_item = QListWidgetItem()
        list_item.setSizeHint(QSize(MENU_LEFT_WIDTH, MenuLeft.h_))
        self.addItem(list_item)
        self.setItemWidget(list_item, self.all_colls_btn)



        favs_btn = CollectionBtn(
            short_name=Lang.fav_coll,
            coll_name=NAME_FAVS
            )
        cmd_ = lambda: self.collection_btn_cmd(favs_btn)
        favs_btn.pressed_.connect(cmd_)

        list_item = QListWidgetItem()
        list_item.setSizeHint(QSize(MENU_LEFT_WIDTH, MenuLeft.h_))
        self.addItem(list_item)
        self.setItemWidget(list_item, favs_btn)

        fake_item = QListWidgetItem()
        list_item.setSizeHint(QSize(MENU_LEFT_WIDTH, MenuLeft.h_))
        fake_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.addItem(fake_item)

        for data in menus:

            coll_btn = CollectionBtn(
                short_name=data.get("short_name"),
                coll_name=data.get("coll_name")
                )
            cmd_ = lambda wid=coll_btn: self.collection_btn_cmd(wid)
            coll_btn.pressed_.connect(cmd_)

            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(MENU_LEFT_WIDTH, MenuLeft.h_))
            self.addItem(list_item)
            self.setItemWidget(list_item, coll_btn)

            if coll_btn.coll_name == JsonData.curr_coll:
                coll_btn.style_solid()
                self.selected_btn = coll_btn
            else:
                coll_btn.style_normal()

