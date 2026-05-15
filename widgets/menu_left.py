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
    def __init__(self, rel_path: str, other):
        super().__init__(other)
        self.rel_path = rel_path


class TreeWid(QTreeWidget):
    tree_reveal = pyqtSignal(str)
    tree_open = pyqtSignal(str)

    svg_folder = "./images/folder.svg"
    svg_size = 16
    item_height = 25

    def __init__(self):
        super().__init__()
        self.selected_path: str = None
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
            rel_path = Utils.get_rel_any_path(
                mf_path=Mf.current_mf.get_avaiable_mf_path(),
                abs_img_path=path
            )
            parent = os.path.dirname(path) or os.sep
            name = os.path.basename(path)
            parent_rel_path = Utils.get_rel_any_path(
                mf_path=Mf.current_mf.get_avaiable_mf_path(),
                abs_img_path=parent
            )
            if Tools.is_hide_digits(Mf.current_mf, parent_rel_path):
                old_name = name
                name = self.strip_to_first_letter(name)
                if not name:
                    name = old_name

            parent_item = self.items.get(parent)
            if parent_item is None:
                continue

            child = UTreeWidgetItem(rel_path, [name])
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
        self.selected_path = path
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
                # Это нужно потому, что в запросах к БД формируется
                # шаблон вида `path + '/%'` (ILIKE/LIKE).
                # Если хранить корень как `'/'`,
                # шаблон превратится в `'//%'` — поиск будет неверным.
                # Пустая строка даёт корректный шаблон `'/%'`,
                # то есть все записи из корня.
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

        abs_path = ""
        if item:
            abs_path = item.data(0, Qt.ItemDataRole.UserRole)
            self.selected_path = abs_path
            view = QAction(Lng.open[Cfg.lng_index], menu)
            view.triggered.connect(lambda: self.tree_open.emit(abs_path))
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

        if item.rel_path:

            if Tools.is_hide_digits(Mf.current_mf, item.rel_path):
                text = Lng.show_digits[Cfg.lng_index]
                cmd = show_digits_cmd
            else:
                text = Lng.hide_digits[Cfg.lng_index]
                cmd = hide_digits_cmd
            hide_ = QAction(text, menu)
            hide_.triggered.connect(cmd)
            menu.addAction(hide_)

            if item.rel_path == os.sep:
                reset_digits = QAction(Lng.show_digits_all[Cfg.lng_index], menu)
                reset_digits.triggered.connect(reset_all_digits_cmd)
                menu.addAction(reset_digits)

        menu.addSeparator()

        reveal = QAction(Lng.reveal_in_finder[Cfg.lng_index], menu)
        reveal.triggered.connect(lambda: self.tree_reveal.emit(abs_path))
        menu.addAction(reveal)

        menu.show_menu()

        return super().contextMenuEvent(a0)


class MfListItem(UListWidgetItem):
    def __init__(self, parent, height = 30, text = None):
        super().__init__(parent, height, text)
        self.mf: Mf = None


# class MenuLeft(QTabWidget):
#     reload_thumbnails = pyqtSignal()
#     no_connection = pyqtSignal(Mf)
#     mf_edit = pyqtSignal(SettingsItem)
#     mf_new = pyqtSignal(SettingsItem)

#     def __init__(self):
#         super().__init__()
#         self.setAcceptDrops(True)
#         self.init_ui()

#     def init_ui(self):

#         def with_conn(fn: callable):
#             def wrapper(mf: Mf, *args, **kwargs):
#                 fn(mf, *args, **kwargs)
#                 avaiable_path = mf.get_avaiable_mf_path()
#                 if not avaiable_path:
#                     self.no_connection.emit(mf)
#                 else:
#                     mf.set_mf_current_path(avaiable_path)
#             return wrapper

#         @with_conn
#         def _mf_reveal(mf: Mf):
#             subprocess.Popen(["open", mf.mf_current_path])

#         @with_conn
#         def _tree_reveal(mf: Mf, rel_path: str):
#             abs_path = Utils.get_abs_any_path(mf.mf_current_path, rel_path)
#             subprocess.Popen(["open", abs_path])

#         def _mf_open(mf: Mf):
#             if Mf.current_mf == mf:
#                 return
#             Mf.current_mf = mf
#             # Корневая директория представляется пустой строкой.
#             # Это нужно потому, что в запросах к БД формируется шаблон вида `path + '/%'` (ILIKE/LIKE).
#             # Если хранить корень как `'/'`, шаблон превратится в `'//%'` — поиск будет неверным.
#             # Пустая строка даёт корректный шаблон `'/%'`, то есть все записи из корня.
#             Dynamic.history.clear()
#             Dynamic.current_dir = ""
#             self.tree_wid.init_ui()
#             self.reload_thumbnails.emit()

#         def _tree_open(mf: Mf, rel_path: str):
#             try:
#                 curr_ind = max(
#                     x
#                     for x, i in enumerate(Dynamic.history)
#                     if i == Dynamic.current_dir
#                 )
#             except ValueError:
#                 curr_ind = -1
#             Dynamic.history = Dynamic.history[:curr_ind + 1]
#             Dynamic.history.append(rel_path)
#             if len(Dynamic.history) > 100:
#                 Dynamic.history = Dynamic.history[-100:]
#             Dynamic.current_dir = rel_path
#             self.reload_thumbnails.emit()

#         def _mf_edit(mf: Mf):
#             item = SettingsItem("edit_folder", mf.mf_alias)
#             self.mf_edit.emit(item)

#         def _mf_new():
#             item = SettingsItem("new_folder", "")
#             self.mf_new.emit(item)

#         self.clear()
#         self.mf_list = MfList(self)
#         self.mf_list.mf_open.connect(lambda mf: _mf_open(mf))
#         self.mf_list.mf_reveal.connect(lambda mf: _mf_reveal(mf))
#         self.mf_list.mf_edit.connect(lambda mf: _mf_edit(mf))
#         self.mf_list.mf_new.connect(lambda: _mf_new())

#         self.tree_wid = TreeWid()
#         self.tree_wid.init_ui()
#         self.tree_wid.tree_reveal.connect(
#             lambda rel_path: _tree_reveal(Mf.current_mf, rel_path)
#         )
#         self.tree_wid.tree_open.connect(
#             lambda rel_path: _tree_open(Mf.current_mf, rel_path)
#         )

#         self.addTab(self.mf_list, Lng.catalogs[Cfg.lng_index])
#         self.addTab(self.tree_wid, Lng.contents[Cfg.lng_index])

#         self.mf_list.setCurrentRow(0)
#         QTimer.singleShot(10, lambda: _mf_open(Mf.current_mf))
    
#     def show_in_app(self, rel_path: str):
#         self.tree_wid.expand_to_path(rel_path)

#     def reload_tree(self):
#         self.tree_wid.init_ui()

#     def dragEnterEvent(self, a0):
#         a0.accept()

#     def dropEvent(self, a0):
#         if a0.mimeData().hasUrls():
#             url = a0.mimeData().urls()[0].toLocalFile().rstrip(os.sep)
#             if os.path.isdir(url):
#                 item = SettingsItem("new_folder", url)
#                 self.mf_new.emit(item)


class MfList(VListWidget):
    mf_open = pyqtSignal(Mf)
    mf_reveal = pyqtSignal(Mf)
    mf_edit = pyqtSignal(Mf)
    mf_new = pyqtSignal()
    svg_folder = "./images/img_folder.svg"
    svg_size = 16

    def __init__(self, parent: QWidget):
        super().__init__(parent=parent)
        self.setCurrentRow(0)
        # self.setDragEnabled(True)
        # self.setAcceptDrops(True)
        # self.setDefaultDropAction(Qt.DropAction.MoveAction)
        # self.setDragDropMode(VListWidget.DragDropMode.InternalMove)
        self.setIconSize(QSize(self.svg_size, self.svg_size))

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
            mf_reveal.triggered.connect(lambda: self.mf_reveal.emit(item.mf))
            menu.addAction(mf_reveal)
            menu.addSeparator()
            mf_edit = QAction(Lng.setup[Cfg.lng_index], menu)
            mf_edit.triggered.connect(lambda: self.mf_edit.emit(item.mf))
            menu.addAction(mf_edit)
        else:
            new_folder = QAction(Lng.new_folder[Cfg.lng_index], menu)
            new_folder.triggered.connect(lambda: self.mf_new.emit())
            menu.addAction(new_folder)
        menu.show_menu()

    def dropEvent(self, event):
        super().dropEvent(event)
        new_order = []
        for i in range(self.count()):
            item: MfListItem = self.item(i)
            new_order.append(item.mf)
        Mf.items = new_order


class MenuLeft(QWidget):
    reload_thumbnails = pyqtSignal()
    reveal_in_finder = pyqtSignal(tuple)
    mf_edit = pyqtSignal(SettingsItem)
    mf_new = pyqtSignal(SettingsItem)
    mf_list_ww = 130

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
        self.tree_wid.init_ui()
        tree_parent.addTab(self.tree_wid, Lng.contents[Cfg.lng_index])

        mf_list_parent = QTabWidget()
        mf_list_parent.tabBar().hide()
        self.splitter.addWidget(mf_list_parent)

        self.mf_list_widget = MfList(mf_list_parent)
        self.mf_list_widget.mf_open.connect(lambda mf: self.mf_open_cmd(mf))
        self.mf_list_widget.mf_reveal.connect(lambda mf: self.mf_reveal_cmd(mf))
        self.mf_list_widget.mf_edit.connect(lambda mf: self.mf_edit_cmd(mf))
        self.mf_list_widget.mf_new
        mf_list_parent.addTab(self.mf_list_widget, Lng.catalogs[Cfg.lng_index])

        self.splitter.setSizes([
            self.height() - self.mf_list_ww,
            self.mf_list_ww
        ])

    def mf_open_cmd(self, mf: Mf):
        Mf.current_mf = mf
        Dynamic.current_dir = ""
        self.reload_thumbnails.emit()

    def mf_reveal_cmd(self, mf: Mf):
        data = (mf, [mf.mf_current_path, ])
        self.reveal_in_finder.emit(data)

    def mf_edit_cmd(self, mf: Mf):
        item = SettingsItem(
            type_="edit_folder",
            content=mf.mf_alias
        )
        self.mf_edit.emit(item)

    def mf_new_cmd(self, mf: Mf):
        ...