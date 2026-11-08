import os
import re

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QVBoxLayout

from cfg import JsonData, Static
from system.items import SettingsItem
from system.lang import Lng
from system.main_folder import Mf
from system.tasks import DbDirsLoader, UThreadPool
from system.utils import Utils

from ._base_widgets import (TransparentFrame, TransparentLabel,
							TransparentWidget, USep, UMenu,
							UTreeWidget, UTreeWidgetItem)


class MenuLeftTreeWidgetItem(UTreeWidgetItem):
	def __init__(self, parent, text, path):
		super().__init__(parent, text)
		self.path = path


class MenuLeftTreeWidget(UTreeWidget):
	load_st_grid = pyqtSignal()
	restart_scaner = pyqtSignal()
	reveal = pyqtSignal(list)
	copy_path = pyqtSignal(list)
	on_tree_clicked = pyqtSignal(str)
	on_hide_digits_clicked = pyqtSignal()
	on_scroll_changed = pyqtSignal(int)

	# компилируем один раз, а не при каждом вызове
	_leading_non_letters = re.compile(r'^[^A-Za-zА-Яа-я]+')

	def __init__(self):
		super().__init__()
		self.itemClicked.connect(self.on_item_click)
		self.verticalScrollBar().valueChanged.connect(self.on_scroll_changed)
		self.abs_selected_path: str = os.sep
		self.items: dict[str, MenuLeftTreeWidgetItem] = {}
		self.stop_paths: set[str] = set()
		self.root_item: MenuLeftTreeWidgetItem | None = None
		# кэш относительных путей из БД, чтобы перестраивать дерево без запроса к БД
		self._paths: list[str] = []

		self.base_folder_icon = QIcon(str(Static.COLOR_ICONS / "base_folder.svg"))
		self.base_stop_list_icon = QIcon(str(Static.COLOR_ICONS / "base_folder_stop_list.svg"))

	def need_hide_digits(self) -> bool:
		return Mf.current_mf.mf_alias in JsonData.hide_digits_mf_lst

	# --- сортировка ---
	def strip_to_first_letter(self, s: str) -> str:
		"""Удаляет начальные символы, которые не являются буквами, для сортировки."""
		return self._leading_non_letters.sub('', s)

	# --- построение ---
	def init_ui(self):
		self.clear()

		root_item = MenuLeftTreeWidgetItem(self, Mf.current_mf.mf_alias, os.sep)
		root_item.setIcon(0, self.base_folder_icon)
		self.addTopLevelItem(root_item)

		task = DbDirsLoader(Mf.current_mf)
		task.sigs.finished_.connect(lambda lst, r=root_item: self.build_tree(r, lst))
		UThreadPool.start(task)

	def build_tree(self, root_item: MenuLeftTreeWidgetItem, paths: list[str]) -> None:
		self.root_item = root_item
		# пути из БД уже относительные: /subfolder/subfolder
		self._paths = [p for p in paths if p != os.sep]
		self._rebuild()

	def _rebuild(self):
		"""
		Перестраивает дочерние элементы корня по кэшу путей.
		Стоп-папка остаётся в дереве с особой иконкой, а её поддерево не создаётся.
		"""
		root = self.root_item
		if root is None:
			return

		root.takeChildren()

		stop_list = set(Mf.current_mf.mf_stop_list)
		hide_digits = self.need_hide_digits()

		# группируем пути по родителю один раз
		children_of: dict[str, list[tuple[str, str]]] = {}
		for path in self._paths:
			parent = os.path.dirname(path) or os.sep
			name = os.path.basename(path)
			# скрываем числовые префиксы только у папок верхнего уровня
			if hide_digits and path.count(os.sep) == 1:
				name = self.strip_to_first_letter(name)
			children_of.setdefault(parent, []).append((name, path))

		self.items = {os.sep: root}
		self.stop_paths = set()
		stack = [os.sep]

		while stack:
			parent_path = stack.pop()
			# поддерево стоп-папки не создаём
			if parent_path in self.stop_paths:
				continue

			parent_item = self.items[parent_path]
			kids = children_of.get(parent_path, [])
			kids.sort(key=lambda kid: self.strip_to_first_letter(kid[0]).lower())

			for name, path in kids:
				is_stop = path in stop_list

				# UTreeWidgetItem(parent, ...) сам добавляет себя к родителю
				child = MenuLeftTreeWidgetItem(parent_item, name, path)
				if is_stop:
					child.setIcon(0, self.base_stop_list_icon)
					self.stop_paths.add(path)
				else:
					child.setIcon(0, self.base_folder_icon)

				self.items[path] = child
				stack.append(path)

		root.setExpanded(True)
		self.expand_to_path(self.abs_selected_path)

	def expand_to_path(self, path: str):
		item = self.items.get(path)
		if item is None:
			return
		self.abs_selected_path = path
		parent = item.parent()
		while parent:
			parent.setExpanded(True)
			parent = parent.parent()
		item.setExpanded(True)
		self.setCurrentItem(item)
		self.scrollToItem(item, UTreeWidget.ScrollHint.PositionAtCenter)

	def on_item_click(self, item: MenuLeftTreeWidgetItem, col: int):
		abs_path = item.path
		if abs_path == self.abs_selected_path:
			return
		self.abs_selected_path = abs_path
		self.on_tree_clicked.emit(abs_path)

	def contextMenuEvent(self, a0):

		def hide_digits_cmd():
			if Mf.current_mf.mf_alias not in JsonData.hide_digits_mf_lst:
				JsonData.hide_digits_mf_lst.append(Mf.current_mf.mf_alias)
				JsonData.write_json_data()
				self._rebuild()
				self.on_hide_digits_clicked.emit()

		def show_digits_cmd():
			if Mf.current_mf.mf_alias in JsonData.hide_digits_mf_lst:
				JsonData.hide_digits_mf_lst.remove(Mf.current_mf.mf_alias)
				JsonData.write_json_data()
				self._rebuild()

		def collapse_all_cmd():
			self.collapseAll()
			self.root_item.setExpanded(True)
			self.setCurrentItem(self.root_item)

		def add_stop_list_cmd():
			if rel_path in Mf.current_mf.mf_stop_list:
				return
			Mf.current_mf.mf_stop_list.append(rel_path)
			Mf.write_json_data()
			self._rebuild()
			self.load_st_grid.emit()

		def rem_stop_list_cmd():
			if rel_path in Mf.current_mf.mf_stop_list:
				Mf.current_mf.mf_stop_list.remove(rel_path)
				Mf.write_json_data()
				print("папка удалена из игнор листа")
			self._rebuild()
			self.restart_scaner.emit()

		item: MenuLeftTreeWidgetItem = self.itemAt(a0.pos())
		menu = UMenu(parent=self)

		rel_path = os.sep
		if item:
			rel_path = item.path  # уже относительный, как в mf_stop_list
			self.abs_selected_path = rel_path
			view = QAction(Lng.open, menu)
			view.triggered.connect(lambda: self.on_tree_clicked.emit(self.abs_selected_path))
			menu.addAction(view)
			menu.addSeparator()

		if self.abs_selected_path == os.sep:
			update = QAction(Lng.update_grid, menu)
			update.triggered.connect(self.init_ui)
			menu.addAction(update)

			menu.addSeparator()

			expand_all = QAction(Lng.expand_all, menu)
			expand_all.triggered.connect(self.expandAll)
			menu.addAction(expand_all)

			collapse_all = QAction(Lng.collapse_all, menu)
			collapse_all.triggered.connect(collapse_all_cmd)
			menu.addAction(collapse_all)

			menu.addSeparator()

			if self.need_hide_digits():
				digits = QAction(Lng.show_digits, menu)
				digits.triggered.connect(show_digits_cmd)
			else:
				digits = QAction(Lng.hide_digits, menu)
				digits.triggered.connect(hide_digits_cmd)
			menu.addAction(digits)

		menu.addSeparator()

		copy_path = QAction(Lng.copy_dirpath, menu)
		copy_path.triggered.connect(lambda: self.copy_path.emit([rel_path]))
		menu.addAction(copy_path)

		reveal = QAction(Lng.reveal_in_finder, menu)
		reveal.triggered.connect(lambda: self.reveal.emit([rel_path]))
		menu.addAction(reveal)

		# корень Mf нельзя добавить в стоп-лист
		if rel_path != os.sep:
			menu.addSeparator()
			if rel_path in Mf.current_mf.mf_stop_list:
				rem_stop_list = QAction(Lng.remove_from_stop_list, menu)
				rem_stop_list.triggered.connect(rem_stop_list_cmd)
				menu.addAction(rem_stop_list)
			else:
				add_stop_list = QAction(Lng.add_stop_list, menu)
				add_stop_list.triggered.connect(add_stop_list_cmd)
				menu.addAction(add_stop_list)

		menu.show_menu_under_cursor(a0)


class MenuLeft(TransparentFrame):
	on_tree_clicked = pyqtSignal(str)
	on_mf_clicked = pyqtSignal(Mf)
	reveal = pyqtSignal(list)
	copy_path = pyqtSignal(list)
	on_hide_digits_clicked = pyqtSignal()
	load_st_grid = pyqtSignal()
	restart_scaner = pyqtSignal()

	def __init__(self):
		super().__init__()
		self.scroll_value = 0

		v_lay = QVBoxLayout(self)
		v_lay.setContentsMargins(0, 0, 0, 0)
		v_lay.setSpacing(0)

		self.tree_wid = MenuLeftTreeWidget()
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
		self.tree_wid.load_st_grid.connect(
			lambda: self.load_st_grid.emit()
		)
		self.tree_wid.restart_scaner.connect(
			lambda: self.restart_scaner.emit()
		)
		self.tree_wid.init_ui()

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