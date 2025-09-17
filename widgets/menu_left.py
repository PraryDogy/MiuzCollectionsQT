import os
import re
import subprocess
from typing import Dict

from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QAction, QTabWidget, QTreeWidget, QTreeWidgetItem

from cfg import Cfg, Dynamic, Static
from system.lang import Lng
from system.main_folder import MainFolder
from system.tasks import SortedDirsLoader, UThreadPool
from system.utils import MainUtils

from ._base_widgets import (SettingsItem, UListWidgetItem, UMenu, UVBoxLayout,
                            VListWidget)


class FavItem(QTreeWidgetItem):
    def __init__(self):
        super().__init__([Lng.favorites[Cfg.lng]])
        self.setData(0, Qt.ItemDataRole.UserRole, None)


class TreeSep(QTreeWidgetItem):
    def __init__(self):
        super().__init__()
        self.setDisabled(True)
        self.setSizeHint(0, QSize(0, 10))
        self.setData(0, Qt.ItemDataRole.UserRole, None)


class TreeWid(QTreeWidget):
    clicked_ = pyqtSignal(str)
    no_connection = pyqtSignal()
    update_grid = pyqtSignal()
    restart_scaner = pyqtSignal()
    hh = 25

    def __init__(self):
        super().__init__()
        self.root_dir: str = None
        self.last_dir: str = None
        self.selected_path: str = None
        self.setHeaderHidden(True)
        self.setAutoScroll(False)
        self.itemClicked.connect(self.on_item_click)

    def init_ui(self, root_dir: str):
        self.clear()
        self.root_dir = root_dir
        self.last_dir = root_dir

        # верхние кастомные элементы
        custom_item = FavItem()
        custom_item.setSizeHint(0, QSize(0, self.hh))
        self.insertTopLevelItem(0, custom_item)

        sep = TreeSep()
        self.insertTopLevelItem(1, sep)

        # корневая директория
        basename = os.path.basename(root_dir)
        root_item = QTreeWidgetItem([basename])
        root_item.setSizeHint(0, QSize(0, self.hh))
        root_item.setData(0, Qt.ItemDataRole.UserRole, root_dir)
        root_item.setToolTip(0, basename + "\n" + root_dir)
        self.addTopLevelItem(root_item)

        worker = SortedDirsLoader(root_dir)
        worker.sigs.finished_.connect(
            lambda data, item=root_item: self.add_children(item, data)
        )
        UThreadPool.start(worker)

    def on_item_click(self, item: QTreeWidgetItem, col: int):
        clicked_dir = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(item, TreeSep):
            return
        elif clicked_dir == self.last_dir:
            return
        elif isinstance(item, FavItem):
            self.last_dir = clicked_dir
            self.selected_path = clicked_dir
            self.clicked_.emit(Static.NAME_FAVS)
        else:
            self.last_dir = clicked_dir
            self.selected_path = clicked_dir
            self.clicked_.emit(clicked_dir)
            if item.childCount() == 0:
                worker = SortedDirsLoader(clicked_dir)
                worker.sigs.finished_.connect(
                    lambda data, item=item: self.add_children(item, data)
                )
                UThreadPool.start(worker)
            item.setExpanded(True)

    def refresh_tree(self):
        if not self.root_dir:
            return
        self.init_ui(self.root_dir)

    def add_children(self, parent_item: QTreeWidgetItem, data: Dict[str, str]) -> None:
        parent_item.takeChildren()
        for path, name in data.items():
            child: QTreeWidgetItem = QTreeWidgetItem([name])
            child.setSizeHint(0, QSize(0, self.hh))
            child.setData(0, Qt.ItemDataRole.UserRole, path)
            child.setToolTip(0, name + "\n" + path)
            parent_item.addChild(child)
        parent_item.setExpanded(True)

        if not self.selected_path:
            return

        paths = self.generate_path_hierarchy(self.selected_path)
        if paths:
            items = self.findItems(
                "*", Qt.MatchFlag.MatchRecursive | Qt.MatchFlag.MatchWildcard
            )
            for it in items:
                for x in paths:
                    if it.data(0, Qt.ItemDataRole.UserRole) == x:
                        self.setCurrentItem(it)
                        break

    def generate_path_hierarchy(self, full_path):
        parts = []
        path = full_path
        while True:
            parts.append(path)
            parent = os.path.dirname(path)
            if parent == path:  # достигли корня
                break
            path = parent
        return parts

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

            update_grid = QAction(Lng.update_grid[Cfg.lng], menu)
            update_grid.triggered.connect(self.update_grid)
            menu.addAction(update_grid)

            restart_scaner = QAction(Lng.scan_folder[Cfg.lng], menu)
            restart_scaner.triggered.connect(self.restart_scaner.emit)
            menu.addAction(restart_scaner)

            menu.addSeparator()

            reveal = QAction(Lng.reveal_in_finder[Cfg.lng], menu)
            reveal.triggered.connect(
                    lambda: self.reveal(path)
                )
            menu.addAction(reveal)

            menu.show_umenu()
        return super().contextMenuEvent(a0)


class MainFolerListItem(UListWidgetItem):
    def __init__(self, parent, height = 30, text = None):
        super().__init__(parent, height, text)
        self.main_folder: MainFolder = None
    

class MainFolderList(VListWidget):
    open_main_folder = pyqtSignal(MainFolder)
    no_connection = pyqtSignal()
    setup_main_folder = pyqtSignal(MainFolder)
    setup_new_folder = pyqtSignal()
    update_grid = pyqtSignal()
    restart_scaner = pyqtSignal()

    def __init__(self, parent: QTabWidget):
        super().__init__(parent=parent)

        for i in MainFolder.list_:
            if i.curr_path:
                true_name = os.path.basename(i.curr_path)
            else:
                true_name = os.path.basename(i.paths[0])
            text = f"{true_name} ({i.name})"
            item = MainFolerListItem(parent=self, text=text)
            item.main_folder = i
            item.setToolTip(i.name + "\n" + i.curr_path)
            self.addItem(item)

        self._last_main_folder = MainFolder.list_[0]
        self.setCurrentRow(0)

    def cmd(self, flag: str, item: MainFolerListItem):
        main_folder = item.main_folder
        main_folder_path = main_folder.get_curr_path()
        if not main_folder_path:
            self.no_connection.emit()
        else:
            if flag == "reveal":
                subprocess.Popen(["open", main_folder_path])
            elif flag == "view":
                self.open_main_folder.emit(main_folder)

    def mouseReleaseEvent(self, e):
        item: MainFolerListItem = self.itemAt(e.pos())
        if not item:
            return

        # --- Игнорируем клик по уже выбранному элементу ---
        # if item.main_folder == self._last_main_folder:
        #     return

        if e.button() == Qt.MouseButton.LeftButton:
            self.cmd("view", item)
            self._last_main_folder = item.main_folder

        return super().mouseReleaseEvent(e)

    def contextMenuEvent(self, a0):
        menu = UMenu(a0)
        item = self.itemAt(a0.pos())
        if item:
            open = QAction(Lng.open[Cfg.lng], menu)
            open.triggered.connect(lambda: self.cmd("view", item))
            menu.addAction(open)
            update_grid = QAction(Lng.update_grid[Cfg.lng], menu)
            update_grid.triggered.connect(self.update_grid)
            menu.addAction(update_grid)
            restart_scaner = QAction(Lng.scan_folder[Cfg.lng], menu)
            restart_scaner.triggered.connect(self.restart_scaner.emit)
            menu.addAction(restart_scaner)
            menu.addSeparator()
            reveal = QAction(Lng.reveal_in_finder[Cfg.lng], menu)
            reveal.triggered.connect(lambda: self.cmd("reveal", item))
            menu.addAction(reveal)
            menu.addSeparator()
            setup = QAction(Lng.setup[Cfg.lng], menu)
            setup.triggered.connect(lambda: self.setup_main_folder.emit(item.main_folder))
            menu.addAction(setup)
        else:
            new_folder = QAction(Lng.new_folder[Cfg.lng], menu)
            new_folder.triggered.connect(self.setup_new_folder.emit)
            menu.addAction(new_folder)
        menu.show_umenu()


class MenuLeft(QTabWidget):
    clicked_ = pyqtSignal()
    no_connection = pyqtSignal()
    setup_main_folder = pyqtSignal(SettingsItem)
    setup_new_folder = pyqtSignal(SettingsItem)
    update_grid = pyqtSignal()
    restart_scaner = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.init_ui()

    def main_folder_clicked(self, main_folder: MainFolder):
        MainFolder.current = main_folder
        main_folder_path = MainFolder.current.get_curr_path()
        if main_folder_path:
            Dynamic.current_dir = main_folder_path
            Dynamic.thumbnails_count = 0
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
        
        def edit_main_folder(main_folder: MainFolder):
            item = SettingsItem()
            item.action_type = item.type_edit_folder
            item.content = main_folder
            self.setup_main_folder.emit(item)
            
        def setup_new_folder():
            item = SettingsItem()
            item.action_type = item.type_new_folder
            item.content = ""
            self.setup_new_folder.emit(item) 
        
        self.clear()

        main_folders = MainFolderList(self)
        main_folders.open_main_folder.connect(self.main_folder_clicked)
        main_folders.no_connection.connect(self.no_connection.emit)
        main_folders.setup_main_folder.connect(edit_main_folder)
        main_folders.setup_new_folder.connect(setup_new_folder)
        main_folders.update_grid.connect(self.update_grid.emit)
        main_folders.restart_scaner.connect(self.restart_scaner.emit)
        self.addTab(main_folders, Lng.folders[Cfg.lng])

        self.tree_wid = TreeWid()
        self.tree_wid.clicked_.connect(self.tree_clicked)
        self.tree_wid.no_connection.connect(self.no_connection.emit)
        self.tree_wid.update_grid.connect(self.update_grid.emit)
        self.tree_wid.restart_scaner.connect(self.restart_scaner.emit)
        self.addTab(self.tree_wid, Lng.images[Cfg.lng])
        
        main_folder_path = MainFolder.current.get_curr_path()
        if main_folder_path:
            self.tree_clicked(main_folder_path)
            self.tree_wid.init_ui(main_folder_path)
            self.setCurrentIndex(1)
            # без таймера не срабатывает
            QTimer.singleShot(0, lambda: self.tree_clicked(main_folder_path))
            
    def dragEnterEvent(self, a0):
        a0.accept()
    
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            url = a0.mimeData().urls()[0].toLocalFile().rstrip("/")
            if os.path.isdir(url):
                item = SettingsItem()
                item.action_type = item.type_new_folder
                item.content = url
                self.setup_main_folder.emit(item)                