import os
import re
import subprocess
from typing import Dict

from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QAction, QTabWidget, QTreeWidget, QTreeWidgetItem

from cfg import Cfg, Dynamic, Static
from system.lang import Lng
from system.main_folder import Mf
from system.tasks import SortedDirsLoader, UThreadPool
from system.utils import Utils

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
    no_connection = pyqtSignal(Mf)
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
            self.no_connection.emit(Mf.current)

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
        self.mf: Mf = None
    

class MfList(VListWidget):
    open_mf = pyqtSignal(Mf)
    no_connection = pyqtSignal(Mf)
    setup_mf = pyqtSignal(Mf)
    setup_new_folder = pyqtSignal()
    update_grid = pyqtSignal()
    restart_scaner = pyqtSignal()

    def __init__(self, parent: QTabWidget):
        super().__init__(parent=parent)

        for i in Mf.list_:
            if i.curr_path:
                true_name = os.path.basename(i.curr_path)
            else:
                true_name = os.path.basename(i.paths[0])
            text = f"{true_name} ({i.name})"
            item = MainFolerListItem(parent=self, text=text)
            item.mf = i
            item.setToolTip(i.name + "\n" + i.curr_path)
            self.addItem(item)

        self._last_mf = Mf.list_[0]
        self.setCurrentRow(0)

    @staticmethod
    def with_conn(fn):
        def wrapper(self: "MfList", item: MainFolerListItem):
            mf = item.mf
            path = mf.get_curr_path()
            if path:
                return fn(self, item, path, mf)
            else:
                self.no_connection.emit(mf)
        return wrapper

    @with_conn
    def view_cmd(self, item, path, mf):
        self.open_mf.emit(mf)

    @with_conn
    def update_grid_cmd(self, item, path, mf):
        self.update_grid.emit()

    @with_conn
    def reveal_cmd(self, item, path, mf):
        subprocess.Popen(["open", path])

    def mouseReleaseEvent(self, e):
        item: MainFolerListItem = self.itemAt(e.pos())
        if not item:
            return

        if e.button() == Qt.MouseButton.LeftButton:
            self.view_cmd(item)
            self._last_mf = item.mf

        return super().mouseReleaseEvent(e)

    def contextMenuEvent(self, a0):
        menu = UMenu(a0)
        item = self.itemAt(a0.pos())
        if item:
            open = QAction(Lng.open[Cfg.lng], menu)
            open.triggered.connect(lambda: self.view_cmd(item))
            menu.addAction(open)
            update_grid = QAction(Lng.update_grid[Cfg.lng], menu)
            update_grid.triggered.connect(lambda: self.update_grid_cmd(item))
            menu.addAction(update_grid)
            restart_scaner = QAction(Lng.scan_folder[Cfg.lng], menu)
            restart_scaner.triggered.connect(self.restart_scaner.emit)
            menu.addAction(restart_scaner)
            menu.addSeparator()
            reveal = QAction(Lng.reveal_in_finder[Cfg.lng], menu)
            reveal.triggered.connect(lambda: self.reveal_cmd(item))
            menu.addAction(reveal)
            menu.addSeparator()
            setup = QAction(Lng.setup[Cfg.lng], menu)
            setup.triggered.connect(lambda: self.setup_mf.emit(item.mf))
            menu.addAction(setup)
        else:
            new_folder = QAction(Lng.new_folder[Cfg.lng], menu)
            new_folder.triggered.connect(self.setup_new_folder.emit)
            menu.addAction(new_folder)
        menu.show_umenu()


class MenuLeft(QTabWidget):
    reload_thumbnails = pyqtSignal()
    no_connection = pyqtSignal(Mf)
    edit_mf = pyqtSignal(SettingsItem)
    setup_new_mf = pyqtSignal(SettingsItem)
    update_grid = pyqtSignal()
    restart_scaner = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.init_ui()

    def mf_clicked(self, mf: Mf):
        Mf.current = mf
        mf_path = Mf.current.get_curr_path()
        if mf_path:
            Dynamic.current_dir = mf_path
            Dynamic.thumbnails_count = 0
            self.reload_thumbnails_cmd(mf_path)
            self.tree_wid.init_ui(mf_path)
        else:
            self.no_connection.emit()
        
    def reload_thumbnails_cmd(self, path: str):
        if path == Static.NAME_FAVS:
            Dynamic.current_dir = Static.NAME_FAVS
        else:
            Dynamic.current_dir = Utils.get_rel_path(Mf.current.curr_path, path)
        self.reload_thumbnails.emit()

    def init_ui(self):
        
        def edit_mf(mf: Mf):
            item = SettingsItem()
            item.action_type = item.type_edit_folder
            item.content = mf
            self.edit_mf.emit(item)
            
        def setup_new_folder():
            item = SettingsItem()
            item.action_type = item.type_new_folder
            item.content = ""
            self.setup_new_mf.emit(item) 
        
        self.clear()

        mfs = MfList(self)
        mfs.open_mf.connect(self.mf_clicked)
        mfs.no_connection.connect(self.no_connection.emit)
        mfs.setup_mf.connect(edit_mf)
        mfs.setup_new_folder.connect(setup_new_folder)
        mfs.update_grid.connect(self.update_grid.emit)
        mfs.restart_scaner.connect(self.restart_scaner.emit)
        self.addTab(mfs, Lng.folders[Cfg.lng])

        self.tree_wid = TreeWid()
        self.tree_wid.clicked_.connect(self.reload_thumbnails_cmd)
        self.tree_wid.no_connection.connect(self.no_connection.emit)
        self.tree_wid.update_grid.connect(self.update_grid.emit)
        self.tree_wid.restart_scaner.connect(self.restart_scaner.emit)
        self.addTab(self.tree_wid, Lng.images[Cfg.lng])
        
        mf_path = Mf.current.get_curr_path()
        if mf_path:
            self.reload_thumbnails_cmd(mf_path)
            self.tree_wid.init_ui(mf_path)
            self.setCurrentIndex(1)
            # без таймера не срабатывает
            QTimer.singleShot(0, lambda: self.reload_thumbnails_cmd(mf_path))
            
    def dragEnterEvent(self, a0):
        a0.accept()
    
    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            url = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
            if os.path.isdir(url):
                item = SettingsItem()
                item.action_type = item.type_new_folder
                item.content = url
                self.edit_mf.emit(item)                