import os
import subprocess
from typing import Literal

import sqlalchemy
from PyQt5.QtCore import QObject, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QMouseEvent
from PyQt5.QtWidgets import (QAction, QLabel, QListWidget, QListWidgetItem,
                             QScrollArea, QTabWidget, QVBoxLayout, QWidget)

from base_widgets import ContextCustom
from cfg import Dynamic, JsonData, Static
from database import THUMBS, Dbase
from lang import Lang
from main_folders import MainFolder
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
        self.setStyleSheet("padding-left: 5px;")
        self.coll_name = coll_name
        self.short_name = short_name
        self.main_folder_index: int = 0 # для win_upload

    def reveal_collection(self, *args) -> None:
        coll_folder = Utils.get_main_folder_path(main_folder=MainFolder.current)
        if not coll_folder:
            OpenWins.smb(parent_=self.window())
            return

        if self.coll_name in (
            Static.NAME_ALL_COLLS, Static.NAME_FAVS, Static.NAME_RECENTS
        ):

            coll = coll_folder

        else:
            coll = os.path.join(coll_folder, self.coll_name)

        subprocess.Popen(["open", coll])

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.pressed_.emit()

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        menu_ = ContextCustom(event=ev)

        reveal_coll = QAction(text=Lang.reveal_in_finder, parent=self)
        reveal_coll.triggered.connect(self.reveal_collection)
        menu_.addAction(reveal_coll)

        menu_.show_menu()


class WorkerSignals(QObject):
    finished_ = pyqtSignal(list)


class LoadMenus(URunnable):
    def __init__(self, main_folder_index: int):
        super().__init__()
        self.main_folder_index = main_folder_index
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

        try:
            self.signals_.finished_.emit(menus)
        except RuntimeError as e:
            Utils.print_err(error=e)


    def load_colls_query(self) -> list[dict]:
        """
        Queries the database to load distinct `THUMBS.c.coll`, processes them, 
        and returns a list of dictionaries containing short and full `THUMBS.c.coll`.

        :return: A sorted list of dictionaries with `short_name` and `coll_name` keys.
        """
        menus: list[dict] = []

        conn = Dbase.engine.connect()
        main_folder_name = MainFolder.list_[self.main_folder_index].name
        q = sqlalchemy.select(THUMBS.c.coll)
        q = q.where(THUMBS.c.brand == main_folder_name)
        q = q.distinct()
        res = conn.execute(q).fetchall()
        conn.close()

        if res:
            res: tuple[str] = (i[0] for i in res if i)

        else:
            print(main_folder_name, "> left menu > load db colls > no data")
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


class MenuTab(QListWidget):
    h_ = 30

    def __init__(self, main_folder_index: int):
        super().__init__()
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.main_folder_index = main_folder_index
        self.coll_btns: list[CollectionBtn] = []
        self.setup_task()

    def setup_task(self):
        self.task_ = LoadMenus(main_folder_index=self.main_folder_index)
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

        Dynamic.curr_coll_name = btn.coll_name
        Dynamic.grid_offset = 0
        Dynamic.resents = False

        SignalsApp.instance.win_main_cmd.emit("set_title")
        SignalsApp.instance.grid_thumbnails_cmd.emit("reload")
        SignalsApp.instance.grid_thumbnails_cmd.emit("to_top")

    def recents_cmd(self, *args):
        Dynamic.curr_coll_name = Static.NAME_ALL_COLLS
        Dynamic.grid_offset = 0
        Dynamic.resents = True

        SignalsApp.instance.win_main_cmd.emit("set_title")
        SignalsApp.instance.grid_thumbnails_cmd.emit("reload")
        SignalsApp.instance.grid_thumbnails_cmd.emit("to_top")

    def init_ui(self, menus: list[dict[str, str]]):

        self.clear()

        # ALL COLLECTIONS
        all_colls_btn = CollectionBtn(
            short_name=Lang.all_colls,
            coll_name=Static.NAME_ALL_COLLS
            )
        cmd_ = lambda: self.collection_btn_cmd(all_colls_btn)
        all_colls_btn.pressed_.connect(cmd_)
        all_colls_item = QListWidgetItem()
        all_colls_item.setSizeHint(QSize(Static.MENU_LEFT_WIDTH, MenuTab.h_))
        self.addItem(all_colls_item)
        self.setItemWidget(all_colls_item, all_colls_btn)
        self.coll_btns.append(all_colls_btn)

        # FAVORITES
        favs_btn = CollectionBtn(
            short_name=Lang.fav_coll,
            coll_name=Static.NAME_FAVS
            )
        cmd_ = lambda: self.collection_btn_cmd(favs_btn)
        favs_btn.pressed_.connect(cmd_)
        favs_item = QListWidgetItem()
        favs_item.setSizeHint(QSize(Static.MENU_LEFT_WIDTH, MenuTab.h_))
        self.addItem(favs_item)
        self.setItemWidget(favs_item, favs_btn)
        self.coll_btns.append(favs_btn)

        # RECENTS
        recents_btn = CollectionBtn(
            short_name=Lang.recents,
            coll_name=Static.NAME_RECENTS
            )
        recents_btn.pressed_.connect(self.recents_cmd)
        recents_item = QListWidgetItem()
        recents_item.setSizeHint(QSize(Static.MENU_LEFT_WIDTH, MenuTab.h_))
        self.addItem(recents_item)
        self.setItemWidget(recents_item, recents_btn)
        self.coll_btns.append(recents_btn)

        # SPACER
        fake_item = QListWidgetItem()
        fake_item.setSizeHint(QSize(Static.MENU_LEFT_WIDTH, MenuTab.h_ // 2))
        fake_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.addItem(fake_item)

        if Dynamic.curr_coll_name == Static.NAME_ALL_COLLS:
            self.setCurrentRow(self.row(all_colls_item))

        elif Dynamic.curr_coll_name == Static.NAME_FAVS:
            self.setCurrentRow(self.row(favs_item))


        for data in menus:

            coll_btn = CollectionBtn(
                short_name=data.get("short_name"),
                coll_name=data.get("coll_name")
                )
            cmd_ = lambda wid=coll_btn: self.collection_btn_cmd(wid)
            coll_btn.pressed_.connect(cmd_)

            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(Static.MENU_LEFT_WIDTH, MenuTab.h_))
            self.addItem(list_item)
            self.setItemWidget(list_item, coll_btn)

            if Dynamic.curr_coll_name == data.get("coll_name"):
                self.setCurrentRow(self.row(list_item))

            self.coll_btns.append(coll_btn)


class MenuLeft(QTabWidget):
    def __init__(self):
        super().__init__()

        self.tabBarClicked.connect(self.tab_cmd)
        self.menu_tabs_list: list[MenuTab] = []

        self.init_ui()
        SignalsApp.instance.menu_left_cmd.connect(self.menu_left_cmd)

        # получаем ширину, основанную на компоновке вкладок основного виджета
        # передаем ширину в глобальную переменную
        wid = self.widget(0)
        Static.MENU_LEFT_WIDTH = wid.sizeHint().width()
        self.setFixedWidth(Static.MENU_LEFT_WIDTH)

    def init_ui(self):
        self.clear()
        self.menu_tabs_list.clear()

        for i in MainFolder.list_:
            main_folder_index = MainFolder.list_.index(i)
            wid = MenuTab(main_folder_index=main_folder_index)
            self.addTab(wid, i.name)
            self.menu_tabs_list.append(wid)
       
        current_index = MainFolder.list_.index(MainFolder.current)
        self.setCurrentIndex(current_index)

    def tab_cmd(self, index: int):
        MainFolder.current = MainFolder.list_[index]
        Dynamic.curr_coll_name = Static.NAME_ALL_COLLS
        Dynamic.grid_offset = 0

        for i in self.menu_tabs_list:
            i.setCurrentRow(0)

        SignalsApp.instance.win_main_cmd.emit("set_title")
        SignalsApp.instance.grid_thumbnails_cmd.emit("reload")
        SignalsApp.instance.grid_thumbnails_cmd.emit("to_top")

    def menu_left_cmd(self, flag: Literal["reload", "select_all_colls"]):
        if flag == "reload":
            self.init_ui()
        elif flag == "select_all_colls":
            for i in self.menu_tabs_list:
                i.setCurrentRow(0)
        else:
            raise Exception("widgets > menu left > wrong flag", flag)

