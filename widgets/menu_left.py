import os
import re
import subprocess
from typing import Dict

from PyQt5.QtCore import QObject, QSize, Qt, QThreadPool, QTimer, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (QAction, QApplication, QGroupBox, QLabel,
                             QPushButton, QTabWidget, QTreeWidget,
                             QTreeWidgetItem, QWidget)

from cfg import Cfg, Dynamic, Static
from system.lang import Lng
from system.main_folder import MainFolder
from system.tasks import LoadCollListTask, LoadSortedDirsTask
from system.utils import UThreadPool, MainUtils

from ._base_widgets import (UHBoxLayout, UListSpaserItem, UListWidgetItem,
                            UMenu, UVBoxLayout, VListWidget, WinChild)
from .win_warn import WinSmb


class MyTree(QTreeWidget):
    clicked_: pyqtSignal = pyqtSignal(str)
    hh = 25

    def __init__(self, root_dir: str) -> None:
        super().__init__()
        # root_dir = "/Users"
        self.root_dir = root_dir
        self.setHeaderHidden(True)
        self.itemClicked.connect(self.on_item_click)
        self.first_load()

    def first_load(self):
        self.clear()
        root_item: QTreeWidgetItem = QTreeWidgetItem([os.path.basename(self.root_dir)])
        root_item.setSizeHint(0, QSize(0, self.hh))
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.root_dir)  # полный путь
        self.addTopLevelItem(root_item)

        worker: LoadSortedDirsTask = LoadSortedDirsTask(self.root_dir)
        worker.sigs.finished_.connect(lambda data, item=root_item: self.add_children(item, data))
        worker.sigs.finished_.connect(self.clearFocus)
        UThreadPool.start(worker)

    def on_item_click(self, item: QTreeWidgetItem, col: int) -> None:
        path: str = item.data(0, Qt.ItemDataRole.UserRole)
        self.clicked_.emit(path)
        if item.childCount() == 0:
            worker: LoadSortedDirsTask = LoadSortedDirsTask(path)
            worker.sigs.finished_.connect(lambda data, item=item: self.add_children(item, data))
            UThreadPool.start(worker)
        item.setExpanded(True)

    def add_children(self, parent_item: QTreeWidgetItem, data: Dict[str, str]) -> None:
        parent_item.takeChildren()  # удаляем заглушку
        for path, name in data.items():
            child: QTreeWidgetItem = QTreeWidgetItem([name])
            child.setSizeHint(0, QSize(0, self.hh))
            child.setData(0, Qt.ItemDataRole.UserRole, path)  # полный путь
            parent_item.addChild(child)
        parent_item.setExpanded(True)


class MainFolderList(VListWidget):
    open_main_folder = pyqtSignal(int)
    double_clicked = pyqtSignal()

    def __init__(self, parent: QTabWidget):
        super().__init__(parent=parent)

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
        if flag == "reveal":
            if not path:
                self.win_warn = WinSmb()
                self.win_warn.center_relative_parent(self.window())
                self.win_warn.show()
            else:
                subprocess.Popen(["open", path])
        elif flag == "view":
            index = MainFolder.list_.index(folder)
            self.open_main_folder.emit(index)

    def mouseReleaseEvent(self, e):
        idx = self.indexAt(e.pos())
        if not idx.isValid():
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self.cmd("view")
        return super().mouseReleaseEvent(e)

    def contextMenuEvent(self, a0):
        menu = UMenu(a0)
        open = QAction(Lng.open[Cfg.lng], menu)
        open.triggered.connect(lambda: self.cmd("view"))
        menu.addAction(open)
        reveal = QAction(Lng.reveal_in_finder[Cfg.lng], menu)
        reveal.triggered.connect(lambda: self.cmd("reveal"))
        menu.addAction(reveal)
        menu.show_()


class MenuLeft(QTabWidget):
    set_window_title = pyqtSignal()
    scroll_to_top = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def open_main_folder(self, index: int):
        MainFolder.current = MainFolder.list_[index]
        Dynamic.curr_coll_name = Static.NAME_ALL_COLLS
        Dynamic.grid_buff_size = 0
        self.collections_list.root_dir = MainFolder.current.curr_path
        self.collections_list.first_load()
        self.set_window_title.emit()
        self.scroll_to_top.emit()
        self.reload_thumbnails.emit()
        
    def clicked_(self, path: str):
        Dynamic.curr_path = MainUtils.get_rel_path(MainFolder.current.curr_path, path)
        self.scroll_to_top.emit()
        self.reload_thumbnails.emit()

    def init_ui(self):
        self.clear()

        main_folders = MainFolderList(self)
        main_folders.open_main_folder.connect(lambda index: self.open_main_folder(index))
        main_folders.double_clicked.connect(lambda: self.setCurrentIndex(1))
        self.addTab(main_folders, Lng.folders[Cfg.lng])

        self.collections_list = MyTree(MainFolder.current.curr_path)
        self.collections_list.clicked_.connect(self.clicked_)
        # self.collections_list.scroll_to_top.connect(self.scroll_to_top.emit)
        # self.collections_list.set_window_title.connect(self.set_window_title.emit)
        # self.collections_list.reload_thumbnails.connect(self.reload_thumbnails.emit)
        self.addTab(self.collections_list, Lng.collection[Cfg.lng])

        self.setCurrentIndex(1)
        