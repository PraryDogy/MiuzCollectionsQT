import os
import re
import subprocess

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QSizePolicy,
                             QVBoxLayout, QWidget)

from cfg import JsonData, Static
from system.items import SettingsItem
from system.lang import Lng
from system.main_folder import Mf
from system.tasks import DbDirsLoader, UThreadPool
from system.utils import Utils

from ._base_widgets import (BaseGrayLabel, BaseSep, UFrame, UListWidget, UMenu,
                            UPushButton, UTreeWidget, UTreeWidgetItem)

ITEM_HEIGHT = 25


class LeftMenuTreeWidgetItem(UTreeWidgetItem):
    def __init__(self, parent, text, path):
        super().__init__(parent, text)
        self.path = path


class LeftMenuTreeWidget(UTreeWidget):
    reveal = pyqtSignal(list)
    copy_path = pyqtSignal(list)
    on_tree_clicked = pyqtSignal(str)
    on_hide_digits_clicked = pyqtSignal()
    
    icon_path = Static.COMMON_ICONS / "base_folder.svg"

    def __init__(self):
        super().__init__()
        self.itemClicked.connect(self.on_item_click)
        self.abs_selected_path: str = os.sep
        self.items: dict[str, LeftMenuTreeWidgetItem] = {}

    def need_hide_digits(self):
        if Mf.current_mf.mf_alias not in JsonData.hide_digits_mf_lst:
            return False
        return True

    # --- сортировка ---
    def strip_to_first_letter(self, s: str) -> str:
        """Удаляет начальные символы, которые не являются буквами, для сортировки."""
        return re.sub(r'^[^A-Za-zА-Яа-я]+', '', s)

    def sort_children(self, parent_item: LeftMenuTreeWidgetItem):
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

        root_item = LeftMenuTreeWidgetItem(self, Mf.current_mf.mf_alias, os.sep)
        root_item.setIcon(0, QIcon(str(self.icon_path)))
        self.addTopLevelItem(root_item)

        task = DbDirsLoader(Mf.current_mf)
        task.sigs.finished_.connect(lambda lst: self.build_tree(root_item, lst))
        UThreadPool.start(task)

    def build_tree(self, root_item: LeftMenuTreeWidgetItem, paths: list[str]) -> None:
        self.items: dict[str, LeftMenuTreeWidgetItem] = {os.sep: root_item}
        hide_digits = self.need_hide_digits()

        for path in sorted(paths):
            if path == os.sep:
                continue
            parent = os.path.dirname(path) or os.sep
            name = os.path.basename(path)

            # Опция: скрывать числовые префиксы только у папок первого (верхнего) уровня
            if hide_digits and path.count(os.sep) == 1:
                name = self.strip_to_first_letter(path)

            parent_item = self.items.get(parent)
            if parent_item is None:
                continue

            child = LeftMenuTreeWidgetItem(parent_item, name, path)
            child.setIcon(0, QIcon(str(self.icon_path)))
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
        self.scrollToItem(item, UTreeWidget.ScrollHint.PositionAtCenter)

    def on_item_click(self, item: LeftMenuTreeWidgetItem, col: int):
        abs_path = item.path
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
            if Mf.current_mf.mf_alias not in JsonData.hide_digits_mf_lst:
                JsonData.hide_digits_mf_lst.append(Mf.current_mf.mf_alias)
                JsonData.write_json_data()
                self.init_ui()
                self.on_hide_digits_clicked.emit()

        def show_digits_cmd():
            if Mf.current_mf.mf_alias in JsonData.hide_digits_mf_lst:
                JsonData.hide_digits_mf_lst.remove(Mf.current_mf.mf_alias)
                JsonData.write_json_data()
                self.init_ui()

        def collapse_all_cmd():
            self.collapseAll()
            first_item = list(self.items.values())[0]
            first_item.setExpanded(True)
            self.setCurrentItem(first_item)

        item: LeftMenuTreeWidgetItem = self.itemAt(a0.pos())
        menu = UMenu(a0)

        abs_path = os.sep
        if item:
            abs_path = item.path
            rel_path = Utils.remove_mf_path(Mf.current_mf.mf_current_path, abs_path)
            self.abs_selected_path = abs_path
            view = QAction(Lng.open[JsonData.lng_index], menu)
            view.triggered.connect(lambda: self.on_tree_clicked.emit(self.abs_selected_path))
            menu.addAction(view)
            menu.addSeparator()

        if self.abs_selected_path == os.sep:
            update = QAction(Lng.update_grid[JsonData.lng_index])
            update.triggered.connect(self.init_ui)
            menu.addAction(update)

            menu.addSeparator()

            expand_all = QAction(Lng.expand_all[JsonData.lng_index], menu)
            expand_all.triggered.connect(lambda: self.expandAll())
            menu.addAction(expand_all)

            collapse_all = QAction(Lng.collapse_all[JsonData.lng_index], menu)
            collapse_all.triggered.connect(lambda: collapse_all_cmd())
            menu.addAction(collapse_all)

            menu.addSeparator()

            if self.need_hide_digits():
                text = Lng.show_digits[JsonData.lng_index]
                cmd = show_digits_cmd
            else:
                text = Lng.hide_digits[JsonData.lng_index]
                cmd = hide_digits_cmd
            digits = QAction(text, menu)
            digits.triggered.connect(cmd)
            menu.addAction(digits)

        menu.addSeparator()

        copy_path = QAction(Lng.copy_dirpath[JsonData.lng_index], menu)
        copy_path.triggered.connect(
            lambda: self.copy_path.emit([rel_path, ])
        )
        menu.addAction(copy_path)

        reveal = QAction(Lng.reveal_in_finder[JsonData.lng_index], menu)
        reveal.triggered.connect(
            lambda: self.reveal.emit([rel_path, ])
        )
        menu.addAction(reveal)

        menu.show_menu()

        return super().contextMenuEvent(a0)


class LeftMenuTitle(BaseGrayLabel):
    def __init__(self):
        super().__init__(text=Lng.folders[JsonData.lng_index])
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class MenuLeft(UFrame):
    on_tree_clicked = pyqtSignal(str)
    reveal = pyqtSignal(list)
    copy_path = pyqtSignal(list)
    on_hide_digits_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.scroll_value = 0

        v_lay = QVBoxLayout(self)
        v_lay.setContentsMargins(0, 0, 0, 0)
        v_lay.setSpacing(0)

        v_lay.addSpacing(5)

        self.left_menu_title = LeftMenuTitle()
        v_lay.addWidget(self.left_menu_title)

        v_lay.addSpacing(5)

        self.tree_wid = LeftMenuTreeWidget()
        v_lay.addWidget(self.tree_wid)
        self.tree_wid.reveal.connect(
            lambda rel_paths: self.reveal.emit(rel_paths)
        )
        self.tree_wid.on_tree_clicked.connect(
            lambda abs_path: self.on_tree_clicked.emit(abs_path)
        )
        self.tree_wid.on_hide_digits_clicked.connect(
            lambda: self.on_hide_digits_clicked.emit()
        )
        self.tree_wid.copy_path.connect(
            lambda rel_paths: self.copy_path.emit(rel_paths)
        )
        self.tree_wid.init_ui()
