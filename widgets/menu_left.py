import os
import re
import subprocess

from PyQt5.QtCore import QSize, Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QAction, QLabel, QTabWidget

from cfg import Dynamic, JsonData, Static
from system.lang import Lang
from system.main_folder import MainFolder
from system.tasks import LoadCollListTask
from system.utils import UThreadPool

from ._base_widgets import UListWidgetItem, UMenu, VListWidget
from .win_warn import WinWarn


class BaseCollBtn(QLabel):
    pressed_ = pyqtSignal()
    lang = (
        ("Все коллекции", "All collections"),

    )

    def __init__(self, text: str):
        self.coll_name = text
        data = {
            Static.NAME_ALL_COLLS: self.lang[0][JsonData.lang_ind],
            Static.NAME_RECENTS: Lang.recents,
            Static.NAME_FAVS: Lang.fav_coll
        }
        if text in data:
            text = data.get(text)
        if JsonData.abc_name:
            text = re.sub(r'^[^A-Za-zА-Яа-я]+', '', text)
        super().__init__(text=text)
        self.setStyleSheet("padding-left: 5px;")


class CollBtn(BaseCollBtn):
    def __init__(self, text: str):
        super().__init__(text)

    def reveal_cmd(self, *args) -> None:
        main_folder_path = MainFolder.current.availability()
        if main_folder_path:
            if self.coll_name in (Static.NAME_ALL_COLLS, Static.NAME_FAVS, Static.NAME_RECENTS):
                coll = main_folder_path
            else:
                coll = os.path.join(main_folder_path, self.coll_name)
            subprocess.Popen(["open", coll])
        else:
            self.win_warn = WinWarn(Lang.no_connection, Lang.no_connection_descr)
            self.win_warn.adjustSize()
            self.win_warn.center_relative_parent(self.window())
            self.win_warn.show()

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.pressed_.emit()

    def contextMenuEvent(self, ev):
        self.context_menu = UMenu(ev)

        preview = QAction(Lang.view, self.context_menu)
        preview.triggered.connect(lambda: self.pressed_.emit())
        self.context_menu.addAction(preview)

        self.context_menu.addSeparator()

        show_in_finder = QAction(Lang.reveal_in_finder, self.context_menu)
        show_in_finder.triggered.connect(lambda: self.reveal_cmd())
        self.context_menu.addAction(show_in_finder)

        self.context_menu.show_()
        return super().contextMenuEvent(ev)


class CollectionList(VListWidget):
    h_ = 30
    scroll_to_top = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    set_window_title = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def collection_btn_cmd(self, btn: CollBtn):
        Dynamic.curr_coll_name = btn.coll_name
        Dynamic.grid_buff_size = 0
        self.set_window_title.emit()
        self.reload_thumbnails.emit()
        self.scroll_to_top.emit()

    def init_ui(self):
        self.task_ = LoadCollListTask(MainFolder.current)
        self.task_.signals_.finished_.connect(self._init_ui)
        UThreadPool.start(self.task_)

    def _init_ui(self, menus: list[str]):
        self.clear()

        # ALL COLLECTIONS
        all_colls_btn = CollBtn(text=Static.NAME_ALL_COLLS)
        cmd_ = lambda: self.collection_btn_cmd(all_colls_btn)
        all_colls_btn.pressed_.connect(cmd_)
        all_colls_item = UListWidgetItem(self)
        self.addItem(all_colls_item)
        self.setItemWidget(all_colls_item, all_colls_btn)

        # FAVORITES
        favs_btn = CollBtn(text=Static.NAME_FAVS)
        cmd_ = lambda: self.collection_btn_cmd(favs_btn)
        favs_btn.pressed_.connect(cmd_)
        favs_item = UListWidgetItem(self)
        self.addItem(favs_item)
        self.setItemWidget(favs_item, favs_btn)

        # RECENTS
        recents_btn = CollBtn(text=Static.NAME_RECENTS)
        cmd_ = lambda: self.collection_btn_cmd(recents_btn)
        recents_btn.pressed_.connect(cmd_)
        recents_item = UListWidgetItem(self)
        self.addItem(recents_item)
        self.setItemWidget(recents_item, recents_btn)

        # SPACER
        spacer = UListWidgetItem(self)
        spacer.setSizeHint(QSize(0, self.h_ // 2))  # 10 — высота отступа
        spacer.setFlags(Qt.NoItemFlags)   # не кликабелен
        self.addItem(spacer)

        self.setCurrentRow(0)

        for i in menus:
            coll_btn = CollBtn(i)
            cmd_ = lambda wid=coll_btn: self.collection_btn_cmd(wid)
            coll_btn.pressed_.connect(cmd_)
            list_item = UListWidgetItem(self)
            self.addItem(list_item)
            self.setItemWidget(list_item, coll_btn)

            if i == Dynamic.curr_coll_name:
                self.setCurrentItem(list_item)

    def contextMenuEvent(self, a0):
        a0.ignore()
        return super().contextMenuEvent(a0)


class MainFolderList(VListWidget):
    open_main_folder = pyqtSignal(int)
    double_clicked = pyqtSignal()

    def __init__(self, parent: QTabWidget):
        super().__init__(parent=parent)
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(lambda: self.cmd("view"))

        for i in MainFolder.list_:
            item = UListWidgetItem(parent=self, text=i.name)
            self.addItem(item)

        self.setCurrentRow(0)

    def cmd(self, flag: str):
        name = self.currentItem().text()
        folder = next((i for i in MainFolder.list_ if i.name == name), None)
        if folder is None:
            return

        path = folder.availability()
        if not path:
            self.win_warn = WinWarn(Lang.no_connection, Lang.no_connection_descr)
            self.win_warn.center_relative_parent(self.window())
            self.win_warn.show()
            return

        if flag == "reveal":
            subprocess.Popen(["open", path])
        elif flag == "view":
            index = MainFolder.list_.index(folder)
            self.open_main_folder.emit(index)

    def mouseReleaseEvent(self, e):
        idx = self.indexAt(e.pos())
        if not idx.isValid():
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self._click_timer.stop()
            self._click_timer.start(300)
        return super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        idx = self.indexAt(e.pos())
        if not idx.isValid():
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self._click_timer.stop()
            self.double_clicked.emit()
        return super().mouseDoubleClickEvent(e)

    def contextMenuEvent(self, a0):
        menu = UMenu(a0)
        open = QAction(Lang.view, menu)
        open.triggered.connect(lambda: self.cmd("view"))
        menu.addAction(open)
        reveal = QAction(Lang.reveal_in_finder, menu)
        reveal.triggered.connect(lambda: self.cmd("reveal"))
        menu.addAction(reveal)
        menu.show_()


class MenuLeft(QTabWidget):
    set_window_title = pyqtSignal()
    scroll_to_top = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    lang = (
        ("Коллекции", "Collections"),

    )
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def open_main_folder(self, index: int):
        MainFolder.current = MainFolder.list_[index]
        Dynamic.curr_coll_name = Static.NAME_ALL_COLLS
        Dynamic.grid_buff_size = 0
        self.collections_list.init_ui()
        self.set_window_title.emit()
        self.scroll_to_top.emit()
        self.reload_thumbnails.emit()

    def init_ui(self):
        self.clear()

        main_folders = MainFolderList(self)
        main_folders.open_main_folder.connect(lambda index: self.open_main_folder(index))
        main_folders.double_clicked.connect(lambda: self.setCurrentIndex(1))
        self.addTab(main_folders, Lang.folders)

        self.collections_list = CollectionList()
        self.collections_list.scroll_to_top.connect(self.scroll_to_top.emit)
        self.collections_list.set_window_title.connect(self.set_window_title.emit)
        self.collections_list.reload_thumbnails.connect(self.reload_thumbnails.emit)
        self.addTab(self.collections_list, self.lang[0][JsonData.lang_ind])

        self.setCurrentIndex(1)
