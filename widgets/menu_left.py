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
from system.tasks import LoadSortedDirsTask, ResetDataTask
from system.utils import MainUtils, UThreadPool

from ._base_widgets import (UHBoxLayout, UListSpacerItem, UListWidgetItem,
                            UMenu, UVBoxLayout, VListWidget, AppModalWindow)


class FavItem(QTreeWidgetItem):
    def __init__(self):
        super().__init__([Lng.favorites[Cfg.lng]])
        self.setData(0, Qt.ItemDataRole.UserRole, "")


class TreeSep(QTreeWidgetItem):
    def __init__(self):
        super().__init__()
        self.setDisabled(True)
        self.setSizeHint(0, QSize(0, 10))
        self.setData(0, Qt.ItemDataRole.UserRole, "")


class TreeWid(QTreeWidget):
    clicked_ = pyqtSignal(str)
    no_connection = pyqtSignal()
    hh = 25

    def __init__(self) -> None:
        super().__init__()
        self.root_dir: str = None
        self.last_dir: str = None
        self.setHeaderHidden(True)
        self.itemClicked.connect(self.on_item_click)

    def init_ui(self, root_dir: str):
        self.clear()
        self.root_dir = root_dir
        self.last_dir = root_dir

        custom_item = FavItem()
        custom_item.setSizeHint(0, QSize(0, self.hh))
        self.insertTopLevelItem(0, custom_item)

        sep = TreeSep()
        self.insertTopLevelItem(1, sep)

        root_item: QTreeWidgetItem = QTreeWidgetItem([os.path.basename(self.root_dir)])
        root_item.setSizeHint(0, QSize(0, self.hh))
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.root_dir)
        self.addTopLevelItem(root_item)

        worker: LoadSortedDirsTask = LoadSortedDirsTask(self.root_dir)
        worker.sigs.finished_.connect(
            lambda data, item=root_item: self.add_children(item, data)
        )
        UThreadPool.start(worker)

    def on_item_click(self, item: QTreeWidgetItem, col: int) -> None:
        clicked_dir = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(item, TreeSep):
            return
        elif clicked_dir == self.last_dir:
            return
        elif isinstance(item, FavItem):
            self.last_dir = clicked_dir
            self.clicked_.emit(Static.NAME_FAVS)
        else:
            self.last_dir = clicked_dir
            self.clicked_.emit(clicked_dir)
            if item.childCount() == 0:
                worker: LoadSortedDirsTask = LoadSortedDirsTask(clicked_dir)
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

            menu.show_umenu()
        return super().contextMenuEvent(a0)


class MainFolderList(VListWidget):
    open_main_folder = pyqtSignal(int)
    double_clicked = pyqtSignal()
    no_connection = pyqtSignal()
    setup_main_folder = pyqtSignal(MainFolder)

    def __init__(self, parent: QTabWidget):
        super().__init__(parent=parent)

        for i in MainFolder.list_:
            text = f"{os.path.basename(i.paths[0])} ({i.name})"
            item = UListWidgetItem(parent=self, text=text)
            item.main_folder = i
            self.addItem(item)

        self.setCurrentRow(0)

    def cmd(self, flag: str, item: UListWidgetItem):
        main_folder: MainFolder = item.main_folder
        main_folder_path = main_folder.get_curr_path()
        if not main_folder_path:
            self.no_connection.emit()
        else:
            if flag == "reveal":
                subprocess.Popen(["open", main_folder_path])
            elif flag == "view":
                index = MainFolder.list_.index(main_folder)
                self.open_main_folder.emit(index)

    def mouseReleaseEvent(self, e):
        item = self.itemAt(e.pos())
        if not item:
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self.cmd("view", item)
        return super().mouseReleaseEvent(e)

    def contextMenuEvent(self, a0):
        item = self.itemAt(a0.pos())
        if not item:
            return

        menu = UMenu(a0)
        open = QAction(Lng.open[Cfg.lng], menu)
        open.triggered.connect(lambda: self.cmd("view", item))
        menu.addAction(open)
        reveal = QAction(Lng.reveal_in_finder[Cfg.lng], menu)
        reveal.triggered.connect(lambda: self.cmd("reveal", item))
        menu.addAction(reveal)
        menu.addSeparator()
        setup = QAction(Lng.setup[Cfg.lng], menu)
        setup.triggered.connect(lambda: self.setup_main_folder.emit(item.main_folder))
        menu.addAction(setup)
        menu.show_umenu()


class MenuLeft(QTabWidget):
    clicked_ = pyqtSignal()
    no_connection = pyqtSignal()
    setup_main_folder = pyqtSignal(MainFolder)
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def main_folder_clicked(self, index: int):
        MainFolder.current = MainFolder.list_[index]
        main_folder_path = MainFolder.current.get_curr_path()
        if main_folder_path:
            Dynamic.current_dir = main_folder_path
            Dynamic.grid_buff_size = 0
            self.tree_clicked(main_folder_path)
            self.tree_wid.init_ui(main_folder_path)
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
        main_folders.setup_main_folder.connect(self.setup_main_folder.emit)
        self.addTab(main_folders, Lng.folders[Cfg.lng])

        self.tree_wid = TreeWid()
        self.tree_wid.clicked_.connect(self.tree_clicked)
        self.tree_wid.no_connection.connect(self.no_connection.emit)
        self.addTab(self.tree_wid, Lng.images[Cfg.lng])
        
        main_folder_path = MainFolder.current.get_curr_path()
        if main_folder_path:
            self.tree_clicked(main_folder_path)
            self.tree_wid.init_ui(main_folder_path)
            self.setCurrentIndex(1)
            # без таймера не срабатывает
            QTimer.singleShot(0, lambda: self.tree_clicked(main_folder_path))