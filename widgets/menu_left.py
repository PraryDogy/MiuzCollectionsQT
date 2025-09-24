import os
import re
import subprocess
from typing import Dict

from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QTabWidget, QTreeWidget, QTreeWidgetItem

from cfg import Cfg, Dynamic, Static
from system.lang import Lng
from system.main_folder import Mf
from system.tasks import DbDirsLoader, SortedDirsLoader, UThreadPool
from system.utils import Utils

from ._base_widgets import (SettingsItem, UListWidgetItem, UMenu, UVBoxLayout,
                            VListWidget)


class TreeWid(QTreeWidget):
    tree_reveal = pyqtSignal(str)
    tree_open = pyqtSignal(str)

    svg_folder = "./images/folder.svg"
    svg_size = 16
    item_height = 25

    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setAutoScroll(False)
        self.setIconSize(QSize(self.svg_size, self.svg_size))
        self.setIndentation(15)
        self.itemClicked.connect(self.on_item_click)

    def reload_ui(self):
        self.init_ui(self.root_dir)

class TreeWid(QTreeWidget):
    tree_reveal = pyqtSignal(str)
    tree_open = pyqtSignal(str)

    svg_folder = "./images/folder.svg"
    svg_size = 16
    item_height = 25

    def __init__(self):
        super().__init__()
        self.root_dir: str = None
        self.last_dir: str = None
        self.selected_path: str = None

        self.setHeaderHidden(True)
        self.setAutoScroll(False)
        self.setIconSize(QSize(self.svg_size, self.svg_size))
        self.setIndentation(15)

        self.itemClicked.connect(self.on_item_click)

    def reload_ui(self):
        self.init_ui()

    def init_ui(self):
        self.clear()

        # if Mf.current.get_curr_path():
        #     root_dir = Mf.current.curr_path
        # else:
        #     root_dir = Mf.current.paths[0]

        # self.root_dir = root_dir
        # self.last_dir = root_dir
        # self.selected_path = root_dir

        root_item = QTreeWidgetItem([Mf.current.name])
        root_item.setSizeHint(0, QSize(0, self.item_height))
        root_item.setData(0, Qt.ItemDataRole.UserRole, "/")
        root_item.setIcon(0, QIcon(self.svg_folder))
        self.addTopLevelItem(root_item)

        # новый таск возвращает список всех директорий
        task = DbDirsLoader(Mf.current)
        task.sigs.finished_.connect(lambda lst: self.build_tree(root_item, lst))
        UThreadPool.start(task)

    def build_tree(self, root_item: QTreeWidgetItem, paths: list[str]) -> None:
        """
        paths — список всех директорий (root + вложенные).
        Строим дерево сразу.
        """
        items: dict[str, QTreeWidgetItem] = {"/": root_item}


        for path in sorted(paths):
            if path == "/":
                continue
            parent = os.path.dirname(path)
            name = os.path.basename(path)

            parent_item = items.get(parent)
            if parent_item is None:
                continue  # защита на случай дыр в списке

            child = QTreeWidgetItem([name])
            child.setIcon(0, QIcon(self.svg_folder))
            child.setSizeHint(0, QSize(0, self.item_height))
            child.setData(0, Qt.ItemDataRole.UserRole, path)
            child.setToolTip(0, f"{name}\n{path}")
            parent_item.addChild(child)

            items[path] = child

        root_item.setExpanded(True)

        # восстановить выделение
        if self.selected_path and self.selected_path in items:
            self.setCurrentItem(items[self.selected_path])

    def on_item_click(self, item: QTreeWidgetItem, col: int):
        clicked_dir = item.data(0, Qt.ItemDataRole.UserRole)
        if clicked_dir and clicked_dir != self.last_dir:
            self.last_dir = clicked_dir
            self.selected_path = clicked_dir
            self.tree_open.emit(clicked_dir)

    def generate_path_hierarchy(self, full_path):
        """Оставил, если нужно для другого кода"""
        parts = []
        path = full_path
        while True:
            parts.append(path)
            parent = os.path.dirname(path)
            if parent == path:
                break
            path = parent
        return parts

    def contextMenuEvent(self, a0):
        item = self.itemAt(a0.pos())
        if item:
            abs_path: str = item.data(0, Qt.ItemDataRole.UserRole)
            menu = UMenu(a0)
            view = QAction(Lng.open[Cfg.lng], menu)
            view.triggered.connect(lambda: self.tree_open.emit(abs_path))
            menu.addAction(view)
            menu.addSeparator()
            reveal = QAction(Lng.reveal_in_finder[Cfg.lng], menu)
            reveal.triggered.connect(lambda: self.tree_reveal.emit(abs_path))
            menu.addAction(reveal)
            menu.show_umenu()
        return super().contextMenuEvent(a0)


class MfListItem(UListWidgetItem):
    def __init__(self, parent, height = 30, text = None):
        super().__init__(parent, height, text)
        self.mf: Mf = None


class MfList(VListWidget):
    mf_edit = pyqtSignal(Mf)
    mf_open = pyqtSignal(Mf)
    mf_reveal = pyqtSignal(Mf)
    mf_new = pyqtSignal()
    svg_folder = "./images/folder.svg"
    svg_size = 16

    def __init__(self, parent: QTabWidget):
        super().__init__(parent=parent)
        self.setCurrentRow(0)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragDropMode(VListWidget.DragDropMode.InternalMove)
        self.setIconSize(QSize(self.svg_size, self.svg_size))

        for i in Mf.list_:
            if i.curr_path:
                true_name = os.path.basename(i.curr_path)
            else:
                true_name = os.path.basename(i.paths[0])
            text = f"{true_name} ({i.name})"
            item = MfListItem(parent=self, text=text)
            item.setIcon(QIcon(self.svg_folder))
            item.mf = i
            item.setToolTip(i.name)
            self.addItem(item)

    def mouseReleaseEvent(self, e):
        item: MfListItem = self.itemAt(e.pos())
        if not item:
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self.mf_open.emit(item.mf)
        return super().mouseReleaseEvent(e)

    def contextMenuEvent(self, a0):
        menu = UMenu(a0)
        item: MfListItem = self.itemAt(a0.pos())
        if item:
            open = QAction(Lng.open[Cfg.lng], menu)
            open.triggered.connect(lambda: self.mf_open.emit(item.mf))
            menu.addAction(open)
            menu.addSeparator()
            reveal = QAction(Lng.reveal_in_finder[Cfg.lng], menu)
            reveal.triggered.connect(lambda: self.mf_reveal.emit(item.mf))
            menu.addAction(reveal)
            menu.addSeparator()
            setup = QAction(Lng.setup[Cfg.lng], menu)
            setup.triggered.connect(lambda: self.mf_edit.emit(item.mf))
            menu.addAction(setup)
        else:
            new_folder = QAction(Lng.new_folder[Cfg.lng], menu)
            new_folder.triggered.connect(lambda: self.mf_new.emit())
            menu.addAction(new_folder)
        menu.show_umenu()

    def dropEvent(self, event):
        super().dropEvent(event)
        new_order = []
        for i in range(self.count()):
            item: MfListItem = self.item(i)
            new_order.append(item.mf)
        Mf.list_ = new_order


class MenuLeft(QTabWidget):
    reload_thumbnails = pyqtSignal()
    no_connection = pyqtSignal(Mf)
    mf_edit = pyqtSignal(SettingsItem)
    mf_new = pyqtSignal(SettingsItem)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):

        def with_conn(fn: callable):
            def wrapper(mf: Mf, *args, **kwargs):
                if mf.get_curr_path():
                    fn(mf, *args, **kwargs)
                else:
                    self.no_connection.emit(mf)
            return wrapper

        @with_conn
        def _mf_reveal(mf: Mf):
            subprocess.Popen(["open", mf.curr_path])

        @with_conn
        def _tree_reveal(mf: Mf, rel_path: str):
            abs_path = Utils.get_abs_path(mf.curr_path, rel_path)
            subprocess.Popen(["open", abs_path])

        def _mf_open(mf: Mf):
            Mf.current = mf
            Dynamic.current_dir = ""
            self.tree_wid.init_ui()
            self.reload_thumbnails.emit()

        def _tree_open(mf: Mf, rel_path: str):
            Dynamic.current_dir = rel_path
            self.reload_thumbnails.emit()

        def _mf_edit(mf: Mf):
            item = SettingsItem()
            item.action_type = item.type_edit_folder
            item.content = mf
            self.mf_edit.emit(item)

        def _mf_new():
            item = SettingsItem()
            item.action_type = item.type_new_folder
            item.content = ""
            self.mf_new.emit(item)

        self.clear()
        self.mf_list = MfList(self)
        self.mf_list.mf_open.connect(lambda mf: _mf_open(mf))
        self.mf_list.mf_reveal.connect(lambda mf: _mf_reveal(mf))
        self.mf_list.mf_edit.connect(lambda mf: _mf_edit(mf))
        self.mf_list.mf_new.connect(lambda: _mf_new())

        self.tree_wid = TreeWid()
        self.tree_wid.init_ui()
        self.tree_wid.tree_reveal.connect(
            lambda rel_path: _tree_reveal(Mf.current, rel_path)
        )
        self.tree_wid.tree_open.connect(
            lambda rel_path: _tree_open(Mf.current, rel_path)
        )

        self.addTab(self.mf_list, Lng.folders[Cfg.lng])
        self.addTab(self.tree_wid, Lng.contents[Cfg.lng])

        self.mf_list.setCurrentRow(0)
        QTimer.singleShot(10, lambda: _mf_open(Mf.current))

    def dragEnterEvent(self, a0):
        a0.accept()

    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            url = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
            if os.path.isdir(url):
                item = SettingsItem()
                item.action_type = item.type_new_folder
                item.content = url
                self.mf_new.emit(item)