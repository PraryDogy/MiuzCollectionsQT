import os
import re
import subprocess
from typing import Dict

from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QTabWidget, QTreeWidget, QTreeWidgetItem

from cfg import Dynamic, cfg
from system.items import SettingsItem
from system.lang import Lng
from system.main_folder import Mf
from system.tasks import DbDirsLoader, UThreadPool
from system.utils import Utils

from ._base_widgets import UListWidgetItem, UMenu, UVBoxLayout, VListWidget


class TreeWid(QTreeWidget):
    tree_reveal = pyqtSignal(str)
    tree_open = pyqtSignal(str)

    svg_folder = "./images/folder.svg"
    svg_size = 16
    item_height = 25

    def __init__(self):
        super().__init__()
        self.selected_path: str = None
        self.items: dict[str, QTreeWidgetItem] = {}

        self.setHeaderHidden(True)
        self.setAutoScroll(False)
        self.setIconSize(QSize(self.svg_size, self.svg_size))
        self.setIndentation(15)

        self.itemClicked.connect(self.on_item_click)

    # --- сортировка ---
    def strip_to_first_letter(self, s: str) -> str:
        """Удаляет начальные символы, которые не являются буквами, для сортировки."""
        return re.sub(r'^[^A-Za-zА-Яа-я]+', '', s)

    def sort_children(self, parent_item: QTreeWidgetItem):
        """Сортировка детей рекурсивно по strip_to_first_letter."""
        children = [parent_item.child(i) for i in range(parent_item.childCount())]
        children.sort(key=lambda it: self.strip_to_first_letter(it.text(0)).lower())

        parent_item.takeChildren()
        for child in children:
            parent_item.addChild(child)
            self.sort_children(child)

    # --- построение ---
    def init_ui(self):
        self.clear()

        root_item = QTreeWidgetItem([Mf.current.alias])
        root_item.setSizeHint(0, QSize(0, self.item_height))
        root_item.setData(0, Qt.ItemDataRole.UserRole, os.sep)
        root_item.setIcon(0, QIcon(self.svg_folder))
        self.addTopLevelItem(root_item)

        task = DbDirsLoader(Mf.current)
        task.sigs.finished_.connect(lambda lst: self.build_tree(root_item, lst))
        UThreadPool.start(task)

    def build_tree(self, root_item: QTreeWidgetItem, paths: list[str]) -> None:
        self.items: dict[str, QTreeWidgetItem] = {os.sep: root_item}

        for path in sorted(paths):
            if path == os.sep:
                continue
            parent = os.path.dirname(path) or os.sep
            name = os.path.basename(path)
            if cfg.hide_digits:
                old_name = name
                name = self.strip_to_first_letter(name)
                if not name:
                    name = old_name

            parent_item = self.items.get(parent)
            if parent_item is None:
                continue

            child = QTreeWidgetItem([name])
            child.setIcon(0, QIcon(self.svg_folder))
            child.setSizeHint(0, QSize(0, self.item_height))
            child.setData(0, Qt.ItemDataRole.UserRole, path)
            child.setToolTip(1, os.path.basename(path))
            parent_item.addChild(child)

            self.items[path] = child

        # сортировка после построения
        self.sort_children(root_item)

        root_item.setExpanded(True)
        self.expand_to_path(self.selected_path)

    def expand_to_path(self, path: str):
        if path == "":
            path = os.sep
        if path not in self.items:
            return
        item = self.items.get(path)
        parent = item.parent()
        while parent:
            parent.setExpanded(True)
            parent = parent.parent()
        item.setExpanded(True)
        self.setCurrentItem(item)
        self.scrollToItem(item, QTreeWidget.ScrollHint.PositionAtCenter)

    def on_item_click(self, item: QTreeWidgetItem, col: int):
        clicked_dir = item.data(0, Qt.ItemDataRole.UserRole)
        if clicked_dir and clicked_dir != self.selected_path:
            self.selected_path = clicked_dir
            if clicked_dir == os.sep:
                # Корневая директория представляется пустой строкой.
                # Это нужно потому, что в запросах к БД формируется шаблон вида `path + '/%'` (ILIKE/LIKE).
                # Если хранить корень как `'/'`, шаблон превратится в `'//%'` — поиск будет неверным.
                # Пустая строка даёт корректный шаблон `'/%'`, то есть все записи из корня.
                clicked_dir = ""
            self.tree_open.emit(clicked_dir)

    def generate_path_hierarchy(self, full_path):
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

        def hide_digits_cmd():
            cfg.hide_digits = not cfg.hide_digits
            self.init_ui()

        def collapse_all_cmd():
            self.collapseAll()
            first_item = list(self.items.values())[0]
            first_item.setExpanded(True)
            self.setCurrentItem(first_item)

        item = self.itemAt(a0.pos())
        menu = UMenu(a0)

        abs_path = ""
        if item:
            abs_path = item.data(0, Qt.ItemDataRole.UserRole)

            view = QAction(Lng.open[cfg.lng], menu)
            view.triggered.connect(lambda: self.tree_open.emit(abs_path))
            menu.addAction(view)
            menu.addSeparator()

        expand_all = QAction(Lng.expand_all[cfg.lng], menu)
        expand_all.triggered.connect(lambda: self.expandAll())
        menu.addAction(expand_all)

        collapse_all = QAction(Lng.collapse_all[cfg.lng], menu)
        collapse_all.triggered.connect(lambda: collapse_all_cmd())
        menu.addAction(collapse_all)

        menu.addSeparator()

        hide_digits = QAction(Lng.hide_digits[cfg.lng], menu)
        hide_digits.triggered.connect(hide_digits_cmd)
        hide_digits.setCheckable(True)
        hide_digits.setChecked(cfg.hide_digits)
        menu.addAction(hide_digits)
        menu.addSeparator()

        reveal = QAction(Lng.reveal_in_finder[cfg.lng], menu)
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
    svg_folder = "./images/img_folder.svg"
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
            text = f"{true_name} ({i.alias})"
            item = MfListItem(parent=self, text=text)
            item.setIcon(QIcon(self.svg_folder))
            item.mf = i
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
            open = QAction(Lng.open[cfg.lng], menu)
            open.triggered.connect(lambda: self.mf_open.emit(item.mf))
            menu.addAction(open)
            menu.addSeparator()
            reveal = QAction(Lng.reveal_in_finder[cfg.lng], menu)
            reveal.triggered.connect(lambda: self.mf_reveal.emit(item.mf))
            menu.addAction(reveal)
            menu.addSeparator()
            setup = QAction(Lng.setup[cfg.lng], menu)
            setup.triggered.connect(lambda: self.mf_edit.emit(item.mf))
            menu.addAction(setup)
        else:
            new_folder = QAction(Lng.new_folder[cfg.lng], menu)
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
                fn(mf, *args, **kwargs)
                if not mf.get_available_path():
                    self.no_connection.emit(mf)
            return wrapper

        @with_conn
        def _mf_reveal(mf: Mf):
            subprocess.Popen(["open", mf.curr_path])

        @with_conn
        def _tree_reveal(mf: Mf, rel_path: str):
            abs_path = Utils.get_abs_any_path(mf.curr_path, rel_path)
            subprocess.Popen(["open", abs_path])

        def _mf_open(mf: Mf):
            if Mf.current == mf:
                return
            Mf.current = mf
            # Корневая директория представляется пустой строкой.
            # Это нужно потому, что в запросах к БД формируется шаблон вида `path + '/%'` (ILIKE/LIKE).
            # Если хранить корень как `'/'`, шаблон превратится в `'//%'` — поиск будет неверным.
            # Пустая строка даёт корректный шаблон `'/%'`, то есть все записи из корня.
            Dynamic.history.clear()
            Dynamic.current_dir = ""
            self.tree_wid.init_ui()
            self.reload_thumbnails.emit()

        def _tree_open(mf: Mf, rel_path: str):
            try:
                curr_ind = max(
                    x
                    for x, i in enumerate(Dynamic.history)
                    if i == Dynamic.current_dir
                )
            except ValueError:
                curr_ind = -1
            Dynamic.history = Dynamic.history[:curr_ind + 1]
            Dynamic.history.append(rel_path)
            if len(Dynamic.history) > 100:
                Dynamic.history = Dynamic.history[-100:]
            Dynamic.current_dir = rel_path
            self.reload_thumbnails.emit()

        def _mf_edit(mf: Mf):
            item = SettingsItem("edit_folder", mf)
            self.mf_edit.emit(item)

        def _mf_new():
            item = SettingsItem("new_folder", "")
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

        self.addTab(self.mf_list, Lng.folders[cfg.lng])
        self.addTab(self.tree_wid, Lng.contents[cfg.lng])

        self.mf_list.setCurrentRow(0)
        QTimer.singleShot(10, lambda: _mf_open(Mf.current))

    def reload_tree(self):
        self.tree_wid.clear()
        self.tree_wid.init_ui()

    def dragEnterEvent(self, a0):
        a0.accept()

    def dropEvent(self, a0):
        if a0.mimeData().hasUrls():
            url = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
            if os.path.isdir(url):
                item = SettingsItem("new_folder", url)
                self.mf_new.emit(item)