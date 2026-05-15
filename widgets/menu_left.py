import os
import re
import subprocess

from PyQt5.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QAction, QSplitter, QTabWidget, QTreeWidget,
                             QTreeWidgetItem, QWidget)

from cfg import Cfg, Dynamic
from system.items import SettingsItem
from system.lang import Lng
from system.main_folder import Mf
from system.tasks import DbDirsLoader, UThreadPool
from system.utils import Utils

from ._base_widgets import (UHBoxLayout, UListWidgetItem, UMenu, UVBoxLayout,
                            VListWidget)


class Tools:

    def hide_digits(mf: Mf, rel_path: str):
        rel_paths = Cfg.hide_digits_list.get(mf.mf_alias, None)
        if rel_paths is None:
            Cfg.hide_digits_list[mf.mf_alias] = [rel_path, ]
        elif isinstance(rel_paths, list) and rel_path not in rel_paths:
            rel_paths.append(rel_path)

    def show_digits(mf: Mf, rel_path: str):
        rel_paths = Cfg.hide_digits_list.get(mf.mf_alias, None)
        if isinstance(rel_paths, list) and rel_path in rel_paths:
            rel_paths.remove(rel_path)
            if len(rel_paths) == 0:
                Cfg.hide_digits_list.pop(mf.mf_alias)

    def reset_all_digits(mf: Mf):
        if mf.mf_alias in Cfg.hide_digits_list:
            Cfg.hide_digits_list.pop(mf.mf_alias)

    def is_hide_digits(mf: Mf, rel_path: str):
        if mf.mf_alias not in Cfg.hide_digits_list:
            return False
        if rel_path not in Cfg.hide_digits_list[mf.mf_alias]:
            return False
        return True


class UTreeWidgetItem(QTreeWidgetItem):
    def __init__(self, abs_path: str, other):
        super().__init__(other)


class TreeWid(QTreeWidget):
    reveal = pyqtSignal(str)
    on_tree_clicked = pyqtSignal(str)

    svg_folder = "./images/folder.svg"
    svg_size = 16
    item_height = 25

    def __init__(self):
        super().__init__()
        self.abs_selected_path: str = os.sep
        self.items: dict[str, UTreeWidgetItem] = {}

        self.setHeaderHidden(True)
        self.setAutoScroll(False)
        self.setIconSize(QSize(self.svg_size, self.svg_size))
        self.setIndentation(15)

        self.itemClicked.connect(self.on_item_click)

    # --- сортировка ---
    def strip_to_first_letter(self, s: str) -> str:
        """Удаляет начальные символы, которые не являются буквами, для сортировки."""
        return re.sub(r'^[^A-Za-zА-Яа-я]+', '', s)

    def sort_children(self, parent_item: UTreeWidgetItem):
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

        root_item = UTreeWidgetItem(os.sep, [Mf.current_mf.mf_alias])
        root_item.setSizeHint(0, QSize(0, self.item_height))
        root_item.setData(0, Qt.ItemDataRole.UserRole, os.sep)
        root_item.setIcon(0, QIcon(self.svg_folder))
        self.addTopLevelItem(root_item)

        task = DbDirsLoader(Mf.current_mf)
        task.sigs.finished_.connect(lambda lst: self.build_tree(root_item, lst))
        UThreadPool.start(task)

    def build_tree(self, root_item: UTreeWidgetItem, paths: list[str]) -> None:
        self.items: dict[str, UTreeWidgetItem] = {os.sep: root_item}

        for path in sorted(paths):
            if path == os.sep:
                continue
            parent = os.path.dirname(path) or os.sep
            name = os.path.basename(path)

            parent_item = self.items.get(parent)
            if parent_item is None:
                continue

            child = UTreeWidgetItem(path, [name])
            child.setIcon(0, QIcon(self.svg_folder))
            child.setSizeHint(0, QSize(0, self.item_height))
            child.setData(0, Qt.ItemDataRole.UserRole, path)
            child.setToolTip(1, os.path.basename(path))
            parent_item.addChild(child)

            self.items[path] = child

        # сортировка после построения
        self.sort_children(root_item)

        root_item.setExpanded(True)
        self.expand_to_path(self.abs_selected_path)

    def expand_to_path(self, path: str):
        if path not in self.items:
            return
        self.abs_selected_path = path
        item = self.items.get(path)
        parent = item.parent()
        while parent:
            parent.setExpanded(True)
            parent = parent.parent()
        item.setExpanded(True)
        self.setCurrentItem(item)
        self.scrollToItem(item, QTreeWidget.ScrollHint.PositionAtCenter)

    def on_item_click(self, item: UTreeWidgetItem, col: int):
        abs_path = item.data(0, Qt.ItemDataRole.UserRole)
        if abs_path == self.abs_selected_path:
            return
        self.abs_selected_path = abs_path
        self.on_tree_clicked.emit(abs_path)

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
            Tools.hide_digits(Mf.current_mf, item.rel_path)
            Cfg.write_json_data()
            self.init_ui()

        def show_digits_cmd():
            Tools.show_digits(Mf.current_mf, item.rel_path)
            Cfg.write_json_data()
            self.init_ui()

        def reset_all_digits_cmd():
            Tools.reset_all_digits(Mf.current_mf)
            Cfg.write_json_data()
            self.init_ui()

        def collapse_all_cmd():
            self.collapseAll()
            first_item = list(self.items.values())[0]
            first_item.setExpanded(True)
            self.setCurrentItem(first_item)

        item: UTreeWidgetItem = self.itemAt(a0.pos())
        menu = UMenu(a0)

        abs_path = os.sep
        if item:
            abs_path = item.data(0, Qt.ItemDataRole.UserRole)
            self.abs_selected_path = abs_path
            view = QAction(Lng.open[Cfg.lng_index], menu)
            view.triggered.connect(lambda: self.on_tree_clicked.emit(self.abs_selected_path))
            menu.addAction(view)
            menu.addSeparator()

        update = QAction(Lng.update_grid[Cfg.lng_index])
        update.triggered.connect(self.init_ui)
        menu.addAction(update)

        expand_all = QAction(Lng.expand_all[Cfg.lng_index], menu)
        expand_all.triggered.connect(lambda: self.expandAll())
        menu.addAction(expand_all)

        collapse_all = QAction(Lng.collapse_all[Cfg.lng_index], menu)
        collapse_all.triggered.connect(lambda: collapse_all_cmd())
        menu.addAction(collapse_all)

        menu.addSeparator()

        menu.addSeparator()

        reveal = QAction(Lng.reveal_in_finder[Cfg.lng_index], menu)
        reveal.triggered.connect(lambda: self.reveal.emit(abs_path))
        menu.addAction(reveal)

        menu.show_menu()

        return super().contextMenuEvent(a0)


class MfListItem(UListWidgetItem):
    def __init__(self, parent, height = 30, text = None):
        super().__init__(parent, height, text)
        self.mf: Mf = None


class MfList(VListWidget):
    mf_open = pyqtSignal(Mf)
    mf_reveal = pyqtSignal(tuple)
    mf_edit = pyqtSignal(Mf)
    mf_new = pyqtSignal(str)
    svg_folder = "./images/img_folder.svg"
    svg_size = 16

    def __init__(self, parent: QWidget):
        super().__init__(parent=parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragDropMode(VListWidget.DragDropMode.InternalMove)
        self.setIconSize(QSize(self.svg_size, self.svg_size))
        self.init_ui()
        self.setCurrentRow(0)

    def init_ui(self):
        for i in Mf.items:
            item = MfListItem(parent=self, text=i.mf_alias)
            item.setIcon(QIcon(self.svg_folder))
            item.mf = i
            self.addItem(item)

    def mouseReleaseEvent(self, e):
        item: MfListItem = self.itemAt(e.pos())
        if not item:
            self.clearSelection()
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self.mf_open.emit(item.mf)
        return super().mouseReleaseEvent(e)

    def contextMenuEvent(self, a0):
        menu = UMenu(a0)
        item: MfListItem = self.itemAt(a0.pos())
        if item:
            mf_open = QAction(Lng.open[Cfg.lng_index], menu)
            mf_open.triggered.connect(lambda: self.mf_open.emit(item.mf))
            menu.addAction(mf_open)
            menu.addSeparator()
            mf_reveal = QAction(Lng.reveal_in_finder[Cfg.lng_index], menu)
            mf_reveal.triggered.connect(
                lambda: self.mf_reveal.emit((item.mf, [item.mf.mf_current_path]))
            )
            menu.addAction(mf_reveal)
            menu.addSeparator()
            mf_edit = QAction(Lng.setup[Cfg.lng_index], menu)
            mf_edit.triggered.connect(lambda: self.mf_edit.emit(item.mf))
            menu.addAction(mf_edit)
        else:
            new_folder = QAction(Lng.new_folder[Cfg.lng_index], menu)
            new_folder.triggered.connect(lambda: self.mf_new.emit(""))
            menu.addAction(new_folder)
        menu.show_menu()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragMoveEvent(e)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            url = urls[0].toLocalFile().rstrip(os.sep)
            if os.path.isdir(url):
                self.mf_new.emit(url)
        else:
            super().dropEvent(event)
            new_order = []
            for i in range(self.count()):
                item = self.item(i)
                if isinstance(item, MfListItem):
                    new_order.append(item.mf)
            if new_order:
                Mf.items = new_order
                Mf.write_json_data()


class MenuLeft(QWidget):
    on_tree_clicked = pyqtSignal(str)
    on_mf_clicked = pyqtSignal(Mf)
    reveal = pyqtSignal(tuple)
    mf_edit = pyqtSignal(SettingsItem)
    mf_new = pyqtSignal(SettingsItem)
    mf_list_hh = 130

    def __init__(self):
        super().__init__()
        v_lay = UHBoxLayout(self)
        v_lay.setContentsMargins(0, 5, 0, 0)
        self.splitter = QSplitter()
        self.splitter.setHandleWidth(15)
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        v_lay.addWidget(self.splitter)

        tree_parent = QTabWidget()
        tree_parent.tabBar().hide()
        self.splitter.addWidget(tree_parent)
        self.tree_wid = TreeWid()
        self.tree_wid.reveal.connect(
            lambda abs_path: self.reveal_cmd(Mf.current_mf, [abs_path, ])
        )
        self.tree_wid.on_tree_clicked.connect(
            lambda abs_path: self.on_tree_clicked.emit(abs_path)
        )
        self.tree_wid.init_ui()
        tree_parent.addTab(self.tree_wid, Lng.contents[Cfg.lng_index])

        mf_list_parent = QTabWidget()
        mf_list_parent.tabBar().hide()
        self.splitter.addWidget(mf_list_parent)

        self.mf_list_widget = MfList(mf_list_parent)
        self.mf_list_widget.mf_open.connect(
            lambda mf: self.on_mf_clicked.emit(mf)
        )
        self.mf_list_widget.mf_edit.connect(lambda mf: self.mf_edit_cmd(mf))
        self.mf_list_widget.mf_new.connect(lambda path: self.mf_new_cmd(path))
        self.mf_list_widget.mf_reveal.connect(lambda data: self.reveal_cmd(*data))
        mf_list_parent.addTab(self.mf_list_widget, Lng.catalogs[Cfg.lng_index])

        self.splitter.setSizes([
            self.height() - self.mf_list_hh,
            self.mf_list_hh
        ])

    def reveal_cmd(self, mf: Mf, rel_paths: list[str]):
        self.reveal.emit((mf, rel_paths))

    def mf_edit_cmd(self, mf: Mf):
        item = SettingsItem(
            type_="edit_folder",
            content=mf.mf_alias
        )
        self.mf_edit.emit(item)

    def mf_new_cmd(self, path: str):
        item = SettingsItem(
            type_="new_folder",
            content=path
        )
        self.mf_new.emit(item)