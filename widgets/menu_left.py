import os
import subprocess
from typing import Literal

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (QAction, QLabel, QListWidget, QListWidgetItem,
                             QTabWidget)

from cfg import Dynamic, Static
from system.lang import Lang
from system.main_folder import MainFolder
from system.tasks import LoadCollectionsTask
from system.utils import UThreadPool

from ._base_widgets import UMenu
from .actions import ShowInFinder
from .win_warn import WinWarn


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

    def reveal_cmd(self, *args) -> None:
        main_folder_path = MainFolder.current.is_available()
        if not main_folder_path:
            self.win_warn = WinWarn(Lang.no_connection, Lang.no_connection_descr)
            self.win_warn.adjustSize()
            self.win_warn.center_relative_parent(self.window())
            self.win_warn.show()
        elif self.coll_name in (Static.NAME_ALL_COLLS, Static.NAME_FAVS, Static.NAME_RECENTS):
            coll = main_folder_path
        else:
            coll = os.path.join(main_folder_path, self.coll_name)
        subprocess.Popen(["open", coll])

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.pressed_.emit()

    def contextMenuEvent(self, ev):
        self.context_menu = UMenu(ev)
        show_in_finder = QAction(Lang.reveal_in_finder, self.context_menu)
        show_in_finder.triggered.connect(lambda: self.reveal_cmd())
        self.context_menu.addAction(show_in_finder)
        self.context_menu.show_()
        return super().contextMenuEvent(ev)


class MenuTab(QListWidget):
    h_ = 30
    scroll_to_top = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    set_window_title = pyqtSignal()

    def __init__(self, main_folder_index: int):
        super().__init__()
        self.horizontalScrollBar().setDisabled(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.main_folder_index = main_folder_index
        self.coll_btns: list[CollectionBtn] = []
        self.setup_task()

    def setup_task(self):
        main_folder = MainFolder.list_[self.main_folder_index]
        self.task_ = LoadCollectionsTask(main_folder)
        self.task_.signals_.finished_.connect(self.init_ui)
        UThreadPool.start(self.task_)

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

        self.set_window_title.emit()
        self.reload_thumbnails.emit()
        self.scroll_to_top.emit()

    def recents_cmd(self, *args):
        Dynamic.curr_coll_name = Static.NAME_ALL_COLLS
        Dynamic.grid_offset = 0
        Dynamic.resents = True

        self.set_window_title.emit()
        self.reload_thumbnails.emit()
        self.scroll_to_top.emit()

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
        spacer = QListWidgetItem()
        spacer.setSizeHint(QSize(0, MenuTab.h_ // 2))  # 10 — высота отступа
        spacer.setFlags(Qt.NoItemFlags)   # не кликабелен
        self.addItem(spacer)

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

    def contextMenuEvent(self, a0):
        a0.ignore()
        return super().contextMenuEvent(a0)


class MenuLeft(QTabWidget):
    set_window_title = pyqtSignal()
    scroll_to_top = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.tabBarClicked.connect(self.tab_cmd)
        self.menu_tabs_list: list[MenuTab] = []
        self.init_ui()

    def init_ui(self):
        self.clear()
        self.menu_tabs_list.clear()

        for i in MainFolder.list_:
            main_folder_index = MainFolder.list_.index(i)
            wid = MenuTab(main_folder_index=main_folder_index)
            wid.set_window_title.connect(lambda: self.set_window_title.emit())
            wid.scroll_to_top.connect(lambda: self.scroll_to_top.emit())
            wid.reload_thumbnails.connect(lambda: self.reload_thumbnails.emit())
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

        self.set_window_title.emit()
        self.reload_thumbnails.emit()
        self.scroll_to_top.emit()

    def menu_left_cmd(self, flag: Literal["reload", "select_all_colls"]):
        if flag == "reload":
            self.init_ui()
        elif flag == "select_all_colls":
            for i in self.menu_tabs_list:
                i.setCurrentRow(0)
        else:
            raise Exception("widgets > menu left > wrong flag", flag)