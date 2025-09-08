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


class FavItem(QTreeWidgetItem):
    def __init__(self):
        super().__init__([Lng.favorites[Cfg.lng]])

        
class MyTree(QTreeWidget):
    clicked_ = pyqtSignal(str)
    no_connection = pyqtSignal()
    hh = 25

    def __init__(self) -> None:
        super().__init__()
        self.root_dir = None
        self.setHeaderHidden(True)
        self.itemClicked.connect(self.on_item_click)

    def init_ui(self):
        self.clear()

        custom_item = FavItem()
        custom_item.setSizeHint(0, QSize(0, self.hh))
        custom_item.setData(0, Qt.ItemDataRole.UserRole, "")
        self.insertTopLevelItem(0, custom_item)

        root_item: QTreeWidgetItem = QTreeWidgetItem([os.path.basename(self.root_dir)])
        root_item.setSizeHint(0, QSize(0, self.hh))
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.root_dir)
        self.addTopLevelItem(root_item)

        worker: LoadSortedDirsTask = LoadSortedDirsTask(self.root_dir)
        worker.sigs.finished_.connect(
            lambda data, item=root_item: self.add_children(item, data)
        )
        worker.sigs.finished_.connect(self.select_first_item)
        UThreadPool.start(worker)

    def on_item_click(self, item: QTreeWidgetItem, col: int) -> None:
        if isinstance(item, FavItem):
            self.clicked_.emit(Static.NAME_FAVS)
        else:
            path: str = item.data(0, Qt.ItemDataRole.UserRole)
            self.clicked_.emit(path)
            if item.childCount() == 0:
                worker: LoadSortedDirsTask = LoadSortedDirsTask(path)
                worker.sigs.finished_.connect(
                    lambda data, item=item: self.add_children(item, data)
                )
                UThreadPool.start(worker)
            item.setExpanded(True)

    def add_children(self, parent_item: QTreeWidgetItem, data: Dict[str, str]) -> None:
        parent_item.takeChildren()
        for path, name in data.items():
            child: QTreeWidgetItem = QTreeWidgetItem([name])
            child.setSizeHint(0, QSize(0, self.hh))
            child.setData(0, Qt.ItemDataRole.UserRole, path)
            parent_item.addChild(child)
        parent_item.setExpanded(True)

    def view(self, path: str):
        self.clicked_.emit(path)

    def reveal(self, path: str):
        if os.path.exists(path):
            subprocess.Popen(["open", path])
        else:
            self.no_connection.emit()

    def select_first_item(self):
        top_item = self.topLevelItem(1)
        if top_item:
            self.setCurrentItem(top_item)
            self.itemClicked.emit(top_item, 0)

    def contextMenuEvent(self, a0):
        item = self.itemAt(a0.pos())
        if item:
            path: str = item.data(0, Qt.ItemDataRole.UserRole)

            menu = UMenu(a0)
            view = QAction(Lng.open[Cfg.lng], menu)
            view.triggered.connect(
                lambda: self.view(path)
            )
            menu.addAction(view)

            reveal = QAction(Lng.reveal_in_finder[Cfg.lng], menu)
            reveal.triggered.connect(
                    lambda: self.reveal(path)
                )
            menu.addAction(reveal)

            menu.show_()
        return super().contextMenuEvent(a0)


class MainFolderList(VListWidget):
    open_main_folder = pyqtSignal(int)
    double_clicked = pyqtSignal()
    no_connection = pyqtSignal()

    def __init__(self, parent: QTabWidget):
        super().__init__(parent=parent)

        for i in MainFolder.list_:
            text = f"{i.name} ({os.path.basename(i.paths[0])})"
            item = UListWidgetItem(parent=self, text=text)
            item.main_folder_name = i.name
            self.addItem(item)

        self.setCurrentRow(0)

    def cmd(self, flag: str):
        name = self.currentItem().main_folder_name
        folder = next((i for i in MainFolder.list_ if i.name == name), None)
        main_folder_path = folder.get_curr_path()
        if not main_folder_path:
            self.no_connection.emit()
        else:
            if flag == "reveal":
                subprocess.Popen(["open", main_folder_path])
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
    clicked_ = pyqtSignal()
    no_connection = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def main_folder_clicked(self, index: int):
        MainFolder.current = MainFolder.list_[index]
        main_folder_path = MainFolder.current.get_curr_path()
        if main_folder_path:
            Dynamic.current_dir = main_folder_path
            Dynamic.grid_buff_size = 0
            self.collections_list.root_dir = main_folder_path
            self.collections_list.init_ui()
            self.clicked_.emit()
        else:
            self.no_connection.emit()
        
    def tree_clicked(self, path: str):
        if path == Static.NAME_FAVS:
            Dynamic.current_dir = Static.NAME_FAVS
        else:
            Dynamic.current_dir = MainUtils.get_rel_path(MainFolder.current.curr_path, path)
        self.clicked_.emit()

    def init_ui(self):
        self.clear()

        main_folders = MainFolderList(self)
        main_folders.open_main_folder.connect(lambda index: self.main_folder_clicked(index))
        main_folders.double_clicked.connect(lambda: self.setCurrentIndex(1))
        main_folders.no_connection.connect(self.no_connection.emit)
        self.addTab(main_folders, Lng.folders[Cfg.lng])

        self.collections_list = MyTree()
        self.collections_list.clicked_.connect(self.tree_clicked)
        self.collections_list.no_connection.connect(self.no_connection.emit)
        self.addTab(self.collections_list, Lng.images[Cfg.lng])
        
        main_folder_path = MainFolder.current.get_curr_path()
        if main_folder_path:
            self.collections_list.root_dir = main_folder_path
            self.collections_list.init_ui()
            self.setCurrentIndex(1)