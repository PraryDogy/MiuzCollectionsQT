import os
import shutil
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (QAction, QContextMenuEvent, QFontMetrics, QIcon,
                         QImage, QPixmap)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QLineEdit, QSizePolicy,
                             QSpacerItem, QSplitter, QTableWidget,
                             QTableWidgetItem, QVBoxLayout)

from cfg import JsonData, Static, Themes
from system.items import SettingsItem
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import MfRemover, ProcessWorker
from system.shared_utils import SharedUtils
from system.tasks import (HashDirSize, HashDirSizeItem, MfDataCleaner,
                          UThreadPool)
from system.themes import ThemeChanger
from system.utils import Utils

from ._base_widgets import (ActiveButton, ConfirmWindow, GrayTextLabel,
                            MfAliasWidget, MfPathWidget, MfStopListWidget,
                            RedButton, RowArrowWidget, 
                            SuperConfirmWindow, TitleTextLabel,
                            TransparentLabel, TransparentWidget, UGroupBox,
                            UListSpacerItem, UListWidget, UListWidgetItem,
                            UMainWindow, UMenu, UPushButton, UScrollVerticalArea,
                            USep, USpinBox, WarningWindow)


def restart_app():
	ProcessWorker.stop_all()
	os.execl(sys.executable, sys.executable, *sys.argv)
	QApplication.exit(0)


class CancelChangesWin(ConfirmWindow):
	def __init__(self, text):
		super().__init__(text)
		self.ok_btn.setText(Lng.do_not_save)
		self.cancel_btn.setText(Lng.go_back)


class SaveGroupBox(TransparentWidget):
	save_clicked = pyqtSignal()
	cancel_clicked = pyqtSignal()
	new_catalog_clicked = pyqtSignal()

	def __init__(self, show_new_catalog: bool = True):
		super().__init__()
		self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

		self.h_lay = QHBoxLayout(self)
		self.h_lay.setContentsMargins(0, 0, 0, 0)
		self.h_lay.setSpacing(5)

		self.new_catalog_btn = UPushButton(Lng.new_catalog)
		self.new_catalog_btn.setIcon(QIcon(str(Static.GRAY_ICONS / "crest_gray.svg")))
		self.new_catalog_btn.setIconSize(QSize(10, 10))
		self.new_catalog_btn.clicked.connect(self.new_catalog_clicked.emit)
		self.new_catalog_btn.setVisible(show_new_catalog)
		self.h_lay.addWidget(self.new_catalog_btn)

		self.h_lay.addStretch()

		self.attention_wid = QSvgWidget(str(Static.GRAY_ICONS / "attention_gray.svg"))
		self.attention_wid.setFixedSize(15, 15)
		self.attention_wid.hide()
		self.h_lay.addWidget(self.attention_wid)

		self.save_text = GrayTextLabel(text=Lng.unsaved_changes)
		self.h_lay.addWidget(self.save_text)
		self.save_text.hide()

		self.h_lay.addSpacing(5)

		self.cancel_button = UPushButton(Lng.close)
		self._fix_cancel_button_width()
		self.cancel_button.clicked.connect(self.cancel_clicked.emit)
		self.h_lay.addWidget(self.cancel_button)

		self.save_button = ActiveButton(Lng.save_changes_text)
		self.save_button.setIcon(QIcon(str(Static.GRAY_ICONS / "diskette_gray.svg")))
		self.save_button.clicked.connect(self.save_clicked.emit)
		self.h_lay.addWidget(self.save_button)

	def _fix_cancel_button_width(self):
		# Ширина по самой широкой подписи из двух возможных
		fm = QFontMetrics(self.cancel_button.font())
		texts = (Lng.close, Lng.cancel)
		text_w = max(fm.horizontalAdvance(t) for t in texts)

		# Учитываем внутренние отступы стиля кнопки
		opt_w = self.cancel_button.sizeHint().width() - fm.horizontalAdvance(self.cancel_button.text())
		self.cancel_button.setFixedWidth(text_w + opt_w)

	def show_warning(self):
		self.attention_wid.show()
		self.save_text.show()
		self.cancel_button.setText(Lng.cancel)

	def hide_warning(self):
		self.attention_wid.hide()
		self.save_text.hide()
		self.cancel_button.setText(Lng.close)


class RebootableSettings(UGroupBox):
	changed = pyqtSignal()
	lang_changed = pyqtSignal()
	SPIN_MAX = 60
	SPIN_MIN = 0

	def __init__(self):
		super().__init__()

		self.lng_index = JsonData.lng_index
		self.scanner_minutes = JsonData.scaner_minutes

		self.rus_flag_icon = QIcon(str(Static.COLOR_ICONS / "rus_flag.svg"))
		self.eng_flag_icon = QIcon(str(Static.COLOR_ICONS / "eng_flag.svg"))

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(0)

		self._create_language_widget(main_layout)
		main_layout.addWidget(USep())

		self._create_scanner_widget(main_layout)
		main_layout.addWidget(USep())

		self._create_reset_widget(main_layout)

	def _create_language_widget(self, layout):
		widget = RowArrowWidget(Lng.language_max)
		widget.set_left_icon(Static.COLOR_ICONS / "language.svg")

		self.lng_btn = UPushButton("")
		self.lng_btn.setIconSize(QSize(17, 17))
		self.lng_btn.setFixedWidth(50)

		menu = UMenu(parent=self)
		self.lang_actions = []

		languages = (
			(Lng.lng_menu_rus, self.rus_flag_icon, 0),
			(Lng.lng_menu_eng, self.eng_flag_icon, 1),
		)

		for title, icon, index in languages:
			action = QAction(title, menu)
			action.setIcon(icon)
			action.setIconVisibleInMenu(True)
			action.setCheckable(True)
			action.triggered.connect(
				lambda checked=False, i=index: self.set_language(i)
			)

			menu.addAction(action)
			self.lang_actions.append(action)

			if index == self.lng_index:
				action.setChecked(True)

		self.lng_btn.setMenu(menu)
		widget.replace_arrow_widget(self.lng_btn)

		layout.addWidget(widget)

		self._update_language_icon()
		self._update_language_checked()
		widget.setFixedHeight(self.lng_btn.height() + 4)

	def _create_scanner_widget(self, layout):
		widget = RowArrowWidget(Lng.search_interval)
		widget.set_left_icon(Static.COLOR_ICONS / "clock.svg")
		widget.setFixedHeight(widget.height() + 1)

		self.spin = USpinBox(self)
		self.spin.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
		self.spin.setRange(self.SPIN_MIN, self.SPIN_MAX)
		self.spin.findChild(QLineEdit).setTextMargins(3, 0, 3, 0)
		self.spin.setSuffix(f" {Lng.minutes}")
		self.spin.setValue(self.scanner_minutes)

		self.spin.valueChanged.connect(self.change_scan_time)

		widget.replace_arrow_widget(self.spin)
		layout.addWidget(widget)

	def _create_reset_widget(self, layout):
		widget = RowArrowWidget(Lng.erase_data)
		widget.set_left_icon(Static.COLOR_ICONS / "eraser.svg")
		widget.clicked.connect(self.erase_all_data)

		layout.addWidget(widget)

	def set_language(self, index):
		if self.lng_index == index:
			return

		self.lng_index = index
		self._update_language_icon()
		self._update_language_checked()

		self.changed.emit()
		self.lang_changed.emit()

	def _update_language_icon(self):
		icon = self.rus_flag_icon if self.lng_index == 0 else self.eng_flag_icon
		self.lng_btn.setIcon(icon)

	def _update_language_checked(self):
		for i, action in enumerate(self.lang_actions):
			action.setChecked(i == self.lng_index)

	def change_scan_time(self, value: int):
		if value == self.SPIN_MAX:
			self.spin.blockSignals(True)
			self.spin.setValue(self.SPIN_MIN + 1)
			self.spin.blockSignals(False)
			value = self.SPIN_MIN
		elif value == self.SPIN_MIN:
			self.spin.blockSignals(True)
			self.spin.setValue(self.SPIN_MAX - 1)
			self.spin.blockSignals(False)
			value = self.SPIN_MAX

		self.scanner_minutes = value
		self.changed.emit()

	def erase_all_data(self, *args):

		def fin():
			self.hide()
			shutil.rmtree(Static.APP_DATA_DIR, ignore_errors=True)
			restart_app()

		reset_win = ConfirmWindow(Lng.erase_data_long)
		reset_win.center_to_parent(self.window())
		reset_win.ok_clicked.connect(fin)
		reset_win.show()


class SizesWin(UMainWindow):
	def __init__(self, size_items: list[HashDirSizeItem], parent=None):
		super().__init__(parent)
		self.set_always_on_top()
		self.set_close_only()
		self.setWindowTitle(Lng.data_size)
		self.resize(500, 330)
		self.central_layout.setSpacing(10)

		total_size = SharedUtils.get_f_size(sum(
			item.size for item in size_items
		))
		first_row = TransparentLabel(f"{Lng.data_size}: {total_size}")
		self.central_layout.addWidget(first_row)

		total = sum(item.total_images for item in size_items)
		sec_row = TransparentLabel(f"{Lng.images}: {total}")
		self.central_layout.addWidget(sec_row)

		headers = [
			Lng.folder,
			Lng.file_size,
			Lng.images
		]
		self.table = QTableWidget()
		self.table.setSortingEnabled(True)
		self.table.setColumnCount(len(headers))
		self.table.setHorizontalHeaderLabels(headers)
		self.table.setRowCount(len(size_items))
		self.table.verticalHeader().hide()
		self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignVCenter)
		self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
		self.table.horizontalScrollBar().setDisabled(True)
		self.table.horizontalScrollBar().hide()

		name_width = self.width() // 2
		other_width = self.width() // 4
		self.table.setColumnWidth(0, name_width)
		self.table.setColumnWidth(1, other_width)
		self.table.setColumnWidth(2, other_width)

		self.central_layout.addWidget(self.table)

		self.populate_table(size_items)
		self.setFocus()

	def populate_table(self, size_items: list[HashDirSizeItem]):
		item_flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
		v_center = Qt.AlignmentFlag.AlignVCenter

		for row, item in enumerate(size_items):
			folder_item = QTableWidgetItem(item.mf.mf_alias)
			folder_item.setFlags(
				Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled
			)
			folder_item.setTextAlignment(
				Qt.AlignmentFlag.AlignLeft | v_center
			)

			size_item = QTableWidgetItem(SharedUtils.get_f_size(item.size))
			size_item.setFlags(item_flags)
			size_item.setTextAlignment(
				Qt.AlignmentFlag.AlignLeft | v_center
			)

			total_item = QTableWidgetItem(str(item.total_images))
			total_item.setFlags(item_flags)
			total_item.setTextAlignment(
				Qt.AlignmentFlag.AlignLeft | v_center
			)

			self.table.setItem(row, 0, folder_item)
			self.table.setItem(row, 1, size_item)
			self.table.setItem(row, 2, total_item)

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self.deleteLater()
		return super().keyPressEvent(a0)


class NonRebootableSettings(UGroupBox):
	def __init__(self):
		super().__init__()
		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(0)

		self.size_items = {}

		data_size_wid = RowArrowWidget(Lng.statistic)
		data_size_wid.set_left_icon(Static.COLOR_ICONS / "hdd.svg")
		data_size_wid.clicked.connect(self.show_sizes_win)
		main_layout.addWidget(data_size_wid)

		main_layout.addWidget(USep())

		show_files_wid = RowArrowWidget(Lng.show_system_files)
		show_files_wid.set_left_icon(Static.COLOR_ICONS / "finder.svg")
		show_files_wid.clicked.connect(self.show_files_cmd)
		main_layout.addWidget(show_files_wid)

		self.get_sizes()

	def show_sizes_win(self, *args):
		self.sizes_win = SizesWin(self.size_items)
		self.sizes_win.center_to_parent(self.window())
		self.sizes_win.show()

	def get_sizes(self):
		def on_finish(items: list[HashDirSizeItem]):
			self.size_items = items
		self.hashdir_size = HashDirSize()
		self.hashdir_size.sigs.finished_.connect(on_finish)
		UThreadPool.start(self.hashdir_size)

	def show_files_cmd(self, *args):
		try:
			subprocess.Popen(["open", Static.APP_DATA_DIR])
		except Exception as e:
			print(e)


class ThemeBtn(TransparentWidget):
	clicked = pyqtSignal()

	def __init__(self, theme_name: str, svg_paths: list[Path]):
		super().__init__()
		self.theme_name = theme_name
		self.svg_1, self.svg_2 = svg_paths

		self.setFixedSize(70, 70)

		layout_ = QVBoxLayout(self)
		layout_.setContentsMargins(0, 0, 0, 0)
		layout_.setSpacing(5)

		self.svg_widget = QSvgWidget()
		self.svg_widget.setFixedSize(40, 40)
		layout_.addWidget(self.svg_widget, alignment=Qt.AlignmentFlag.AlignCenter)

		self.title_label = TransparentLabel(self.theme_name)
		layout_.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)

		self.clear_selection()

	def select(self):
		self.svg_widget.load(str(self.svg_2))

	def clear_selection(self):
		self.svg_widget.load(str(self.svg_1))

	def mouseReleaseEvent(self, a0):
		if a0.button() == Qt.MouseButton.LeftButton:
			self.clicked.emit()
		return super().mouseReleaseEvent(a0)

	def enterEvent(self, event):
		self.setCursor(Qt.CursorShape.PointingHandCursor)
		return super().enterEvent(event)


class ThemesWidget(UGroupBox):
	def __init__(self):
		super().__init__()
		main_lay = QVBoxLayout(self)
		main_lay.setContentsMargins(0, 0, 0, 0)
		main_lay.setSpacing(0)

		title_wid = RowArrowWidget(Lng.theme)
		title_wid.set_left_icon(Static.COLOR_ICONS / "theme.svg")
		title_wid.hide_arrow()
		main_lay.addWidget(title_wid)

		main_lay.addWidget(USep())
		main_lay.addSpacing(5)

		themes_wid = TransparentWidget()
		themes_layout = QHBoxLayout(themes_wid)
		themes_layout.setContentsMargins(0, 0, 0, 0)
		themes_layout.setSpacing(5)
		themes_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
		main_lay.addWidget(themes_wid)

		themes_mappings = (
			(Themes.theme_auto, Lng.theme_auto,
				Static.COLOR_ICONS / "theme_auto_1.svg",
				Static.COLOR_ICONS / "theme_auto_2.svg"),
			(Themes.theme_light, Lng.theme_light,
				Static.COLOR_ICONS / "theme_light_1.svg",
				Static.COLOR_ICONS / "theme_light_2.svg"),
			(Themes.theme_dark, Lng.theme_dark,
				Static.COLOR_ICONS / "theme_dark_1.svg",
				Static.COLOR_ICONS / "theme_dark_2.svg"),
		)

		self.selected_theme = JsonData.theme
		self.theme_btns = []

		for theme_type, theme_name, svg_1, svg_2 in themes_mappings:
			btn = ThemeBtn(theme_name, (svg_1, svg_2))
			btn.clicked.connect(
				lambda t=theme_type, b=btn: self.on_btn_clicked(t, b)
			)
			themes_layout.addWidget(btn)
			self.theme_btns.append((theme_type, btn))

		self._refresh_selection()

	def _refresh_selection(self):
		for theme_type, btn in self.theme_btns:
			if theme_type == self.selected_theme:
				btn.select()
			else:
				btn.clear_selection()

	def on_btn_clicked(self, theme_type: str, btn: ThemeBtn):
		if theme_type == self.selected_theme:
			return
		self.selected_theme = theme_type
		self._refresh_selection()
		# Тема сразу сохраняется и применяется, без участия в несохранённых изменениях
		JsonData.theme = theme_type
		JsonData.write_json_data()
		ThemeChanger.init()


class AboutWidLabel(TransparentLabel):
	txt = "\n".join([
		f"Version {Static.APP_VERSION}",
		"Developed by Evlosh",
		"email: evlosh@gmail.com",
		"telegram: evlosh",
		])

	def __init__(self, parent):
		super().__init__(parent=parent)
		self.setMinimumWidth(30)
		self.setText(self.txt)
		self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
		self.setCursor(Qt.CursorShape.IBeamCursor)

	def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
		context_menu = UMenu(parent=self)

		copy_text = QAction(parent=context_menu, text=Lng.copy)
		copy_text.triggered.connect(self.copy_text_md)
		context_menu.addAction(copy_text)

		context_menu.addSeparator()

		select_all = QAction(parent=context_menu, text=Lng.copy_all)
		select_all.triggered.connect(lambda: Utils.pyqt_copy_text(self.text()))
		context_menu.addAction(select_all)

		context_menu.show_menu_under_cursor(ev)

	def copy_text_md(self):
		Utils.pyqt_copy_text(self.selectedText())


class AboutWid(UGroupBox):
	def __init__(self):
		super().__init__()
		h_lay = QHBoxLayout(self)
		h_lay.setContentsMargins(0, 0, 0, 0)
		h_lay.setSpacing(0)

		icon = TransparentLabel()
		qimage = QImage(str(Static.APP_ICONS / "icon.png"))
		qimage_scaled = Utils.scale_qimage_dpr(qimage, 85)
		pixmap = QPixmap.fromImage(qimage_scaled)
		icon.setPixmap(pixmap)
		h_lay.addWidget(icon)

		h_lay.addSpacerItem(QSpacerItem(0, 20))

		lbl = AboutWidLabel(self)
		h_lay.addWidget(lbl)

		h_lay.addStretch()

		if not self.icon_path.exists():
			print("win settings about wid, icon.png not exists")


class GeneralSettings(TransparentWidget):
	lang_changed = pyqtSignal()
	changed = pyqtSignal()

	def __init__(self):
		super().__init__()

		v_lay = QVBoxLayout(self)
		v_lay.setSpacing(10)
		v_lay.setContentsMargins(0, 0, 0, 0)

		self.rebootable_settings = RebootableSettings()
		self.rebootable_settings.changed.connect(self.changed.emit)
		self.rebootable_settings.lang_changed.connect(self.lang_changed.emit)
		v_lay.addWidget(self.rebootable_settings)

		v_lay.addWidget(NonRebootableSettings())

		self.themes = ThemesWidget()
		v_lay.addWidget(self.themes)

		v_lay.addWidget(AboutWid())

		self.adjustSize()

	def save_changes(self):
		def fin():
			JsonData.scaner_minutes = self.rebootable_settings.scanner_minutes
			JsonData.lng_index = self.rebootable_settings.lng_index
			JsonData.theme = self.themes.selected_theme
			JsonData.write_json_data()
			restart_app()

		win = ConfirmWindow(Lng.app_will_restarted)
		win.ok_clicked.connect(fin)
		win.center_to_parent(self.window())
		win.show()


class WinSettingsMfAliasTitle(TransparentLabel):
	def __init__(self, text: str):
		super().__init__(text)


class MfRepairWidget(UGroupBox):
	start_clicked = pyqtSignal()

	def __init__(self, title=None, parent=None):
		super().__init__(title, parent)
		self.v_lay = QVBoxLayout(self)
		self.v_lay.setContentsMargins(10, 5, 10, 5)
		self.v_lay.setSpacing(2)

		title_layout = TitleTextLabel(
			Lng.repair_catalog_long,
			Static.COLOR_ICONS / "repair.svg"
		)
		self.v_lay.addWidget(title_layout)

		self.v_lay.addWidget(USep())

		descr = GrayTextLabel(Lng.catalog_reindex_warning)
		descr.setWordWrap(True)
		self.v_lay.addWidget(descr)

		button_container = TransparentWidget()
		self.v_lay.addWidget(button_container)
		button_layout = QHBoxLayout(button_container)
		button_layout.setContentsMargins(0, 0, 0, 0)
		button_layout.setSpacing(10)

		self.start_btn = UPushButton(Lng.repair_catalog_short)
		self.start_btn.setIcon(QIcon(str(Static.GRAY_ICONS / "repair_gray.svg")))
		self.start_btn.clicked.connect(self.start_clicked)
		button_layout.addWidget(self.start_btn)

		button_layout.addStretch()

		self.setFixedHeight(self.sizeHint().height())


class MfRemoveWidget(UGroupBox):
	start_clicked = pyqtSignal()

	def __init__(self, title=None, parent=None):
		super().__init__(title, parent)
		self.v_lay = QVBoxLayout(self)
		self.v_lay.setContentsMargins(10, 5, 10, 10)
		self.v_lay.setSpacing(5)

		title_layout = TitleTextLabel(
			Lng.remove_folder,
			Static.GRAY_ICONS / "trash_gray.svg"
		)
		self.v_lay.addWidget(title_layout)

		self.v_lay.addWidget(USep())

		descr = GrayTextLabel(Lng.catalog_delete_warning)
		descr.setWordWrap(True)
		self.v_lay.addWidget(descr)

		self.v_lay.addSpacing(3)

		button_container = TransparentWidget()
		self.v_lay.addWidget(button_container)
		button_layout = QHBoxLayout(button_container)
		button_layout.setContentsMargins(0, 0, 0, 0)
		button_layout.setSpacing(10)

		self.start_btn = RedButton(Lng.remove_folder)
		self.start_btn.setIcon(QIcon(str(Static.COLOR_ICONS / "red_trash.svg")))
		self.start_btn.clicked.connect(self.start_clicked)
		button_layout.addWidget(self.start_btn)

		button_layout.addStretch()

		self.setFixedHeight(self.sizeHint().height())


class MfSettings(UScrollVerticalArea):
	changed = pyqtSignal()

	def __init__(self, mf_index: int):
		super().__init__()

		# Получаем объект Mf по индексу
		self.mf = Mf.items[mf_index]

		main_wid = TransparentWidget()
		self.setWidget(main_wid)

		main_lay = QVBoxLayout(main_wid)
		main_lay.setContentsMargins(0, 0, 0, 0)
		main_lay.setSpacing(10)
		self.main_lay = main_lay

		self.path_widget = MfPathWidget(mf=self.mf)
		self.path_widget.changed.connect(self.changed.emit)
		main_lay.addWidget(self.path_widget)

		self.mf_stop_list = MfStopListWidget(mf_stop_list=self.mf.mf_stop_list)
		self.mf_stop_list.changed.connect(self.changed.emit)
		main_lay.addWidget(self.mf_stop_list)

		self.repair_widget = MfRepairWidget()
		self.repair_widget.start_clicked.connect(self.repair_mf)
		main_lay.addWidget(self.repair_widget)

		self.remove_folder = MfRemoveWidget()
		self.remove_folder.start_clicked.connect(self.remove_mf)
		main_lay.addWidget(self.remove_folder)

		main_lay.addStretch()

		self.verticalScrollBar().rangeChanged.connect(self._update_right_margin)
		self._update_right_margin()

	def save_changes(self):
		if not self.path_widget.validate():
			win_warn = WarningWindow(Lng.select_folder_path)
			win_warn.center_to_parent(self.window())
			win_warn.ok_clicked.connect(win_warn.deleteLater)
			win_warn.show()
			return

		def final():
			current_mf = next(
				(i for i in Mf.items if i.mf_alias == self.mf.mf_alias), None
			)
			if current_mf is None:
				return
			current_mf.mf_paths = [self.path_widget.mf_path]
			current_mf.mf_current_path = self.path_widget.mf_path
			current_mf.mf_stop_list = self.mf_stop_list.get_stop_list()
			Mf.write_json_data()
			restart_app()

		win = ConfirmWindow(Lng.app_will_restarted)
		win.ok_clicked.connect(final)
		win.center_to_parent(self.window())
		win.show()

	def _update_right_margin(self, *args):
		# Справа отступ только при видимом скроллбаре
		has_scroll = self.verticalScrollBar().maximum() > 0
		right = 10 if has_scroll else 0
		self.main_lay.setContentsMargins(0, 0, right, 0)

	def remove_mf(self, *args):

		def poll_task():
			if not self.mf_remover.is_alive():
				for i in Mf.items:
					if i.mf_alias == self.mf.mf_alias:
						Mf.items.remove(i)
						break
				if self.mf.mf_alias in JsonData.hide_digits_mf_lst:
					JsonData.hide_digits_mf_lst.remove(self.mf.mf_alias)
					JsonData.write_json_data()
				Mf.write_json_data()
				restart_app()
			else:
				QTimer.singleShot(1000, poll_task)

		def start_mf_remover():
			for i in UMainWindow.win_list:
				i.hide()
			self.mf_remover.start()
			QTimer.singleShot(1000, poll_task)

		self.mf_remover = ProcessWorker(
			target=MfRemover.start,
			args=(self.mf.mf_alias, )
		)

		if len(Mf.items) == 1:
			win = WarningWindow(Lng.at_least_one_folder_required)
		else:
			win = ConfirmWindow(Lng.app_will_restarted)
			win.ok_clicked.connect(start_mf_remover)
		win.center_to_parent(self.window())
		win.show()

	def repair_mf(self, *args):
		def reset_data():
			self.reset_task = MfDataCleaner(self.mf.mf_alias)
			self.reset_task.sigs.finished_.connect(restart_app)
			UThreadPool.start(self.reset_task)

		win = ConfirmWindow(Lng.app_will_restarted)
		win.ok_clicked.connect(reset_data)
		win.center_to_parent(self.window())
		win.show()

	def mouseReleaseEvent(self, a0):
		self.setFocus()
		return super().mouseReleaseEvent(a0)


class NewMfSettings(UMainWindow):
	def __init__(self, mf_path: str = None):
		super().__init__()
		self.setWindowTitle(Lng.new_catalog)
		self.set_always_on_top()
		self.set_close_only()
		self.setMinimumSize(550, 580)

		self.has_unsaved = False
		self.discard_win = None

		self.central_layout.setContentsMargins(10, 10, 10, 10)

		scroll = UScrollVerticalArea()
		self.central_layout.addWidget(scroll)

		main_wid = TransparentWidget()
		scroll.setWidget(main_wid)

		main_lay = QVBoxLayout(main_wid)
		main_lay.setContentsMargins(0, 0, 0, 0)
		main_lay.setSpacing(10)

		self.mf_alias_widget = MfAliasWidget()
		self.mf_alias_widget.changed.connect(self._on_changed)
		main_lay.addWidget(self.mf_alias_widget)

		self.mf_path_widget = MfPathWidget(mf=None)
		self.mf_path_widget.changed.connect(self.mf_path_widget_changed)
		main_lay.addWidget(self.mf_path_widget)

		self.mf_stop_list = MfStopListWidget(mf_stop_list=[])
		self.mf_stop_list.changed.connect(self._on_changed)
		main_lay.addWidget(self.mf_stop_list)

		main_lay.addStretch()

		# Футер с кнопками без «Новый каталог»
		self.save_group = SaveGroupBox(show_new_catalog=False)
		self.save_group.save_clicked.connect(self.save_changes)
		self.save_group.cancel_clicked.connect(self._try_close)
		self.central_layout.addWidget(self.save_group)

		if mf_path:
			self.mf_path_widget_changed()

		self.adjustSize()

	def _on_changed(self):
		self.has_unsaved = True
		self.save_group.show_warning()

	def mf_path_widget_changed(self):
		basename = os.path.basename(self.mf_path_widget.mf_path).capitalize()
		self.mf_alias_widget.line_edit.setText(basename)
		self._on_changed()

	def save_changes(self):
		mf_path = self.mf_path_widget.validate()
		mf_alias = self.mf_alias_widget.validate()

		if not mf_path:
			win_warn = WarningWindow(Lng.select_folder_path)
			win_warn.center_to_parent(self.window())
			win_warn.ok_clicked.connect(win_warn.deleteLater)
			win_warn.show()
			return

		if not mf_alias:
			return

		if any(i.mf_alias == mf_alias for i in Mf.items):
			win_warn = WarningWindow(Lng.alias_already_exists)
			win_warn.center_to_parent(self.window())
			win_warn.ok_clicked.connect(win_warn.deleteLater)
			win_warn.show()
			return

		mf_stop_list = self.mf_stop_list.get_stop_list()

		def fin():
			mf = Mf(
				mf_alias=mf_alias,
				mf_paths=[mf_path],
				mf_stop_list=mf_stop_list,
				mf_current_path=mf_path
			)
			Mf.items.append(mf)
			Mf.write_json_data()
			restart_app()

		win = ConfirmWindow(Lng.app_will_restarted)
		win.ok_clicked.connect(fin)
		win.center_to_parent(self.window())
		win.show()

	def _try_close(self):
		# Кнопка «Отмена» и Esc: сначала проверка несохранённых изменений
		if self.has_unsaved:
			self._ask_discard()
			return
		self.close()

	def _ask_discard(self):
		win = CancelChangesWin(Lng.unsaved_changes_confirm)
		win.ok_clicked.connect(self._on_discard_confirmed)
		win.center_to_parent(self)
		win.show()
		self.discard_win = win  # держим ссылку, чтобы окно не удалилось

	def _on_discard_confirmed(self):
		self.has_unsaved = False
		self.close()

	def closeEvent(self, a0):
		# Крестик окна тоже проходит проверку
		if self.has_unsaved:
			a0.ignore()
			self._ask_discard()
			return
		return super().closeEvent(a0)

	def mouseReleaseEvent(self, a0):
		self.setFocus()
		return super().mouseReleaseEvent(a0)

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self._try_close()
			return
		return super().keyPressEvent(a0)


class WinSettings(UMainWindow):
	closed = pyqtSignal()

	def __init__(self, settings_item: SettingsItem):
		super().__init__()
		self.set_always_on_top()
		self.set_close_only()
		self.setWindowTitle(Lng.settings)
		self.setMinimumSize(730, 600)

		self.settings_item = settings_item
		self.current_page = None
		self.current_idx = 0
		self.pending_idx = None
		self.has_unsaved = False
		self.discard_win = None

		self.central_layout.setContentsMargins(5, 5, 5, 10)

		self.splitter = QSplitter()
		self.splitter.setHandleWidth(15)
		self.splitter.setOrientation(Qt.Orientation.Horizontal)
		self.central_layout.addWidget(self.splitter)

		self.central_layout.addSpacing(10)
		# Единственная кнопка сохранения: футер окна
		self.save_widget = SaveGroupBox()
		self.save_widget.new_catalog_clicked.connect(self.open_new_catalog_win)
		self.save_widget.save_clicked.connect(self.save_settings_cmd)
		self.save_widget.cancel_clicked.connect(self.close)
		self.central_layout.addWidget(self.save_widget)

		self.left_menu = UListWidget()
		self.left_menu.clicked.connect(self.left_menu_click)
		self.splitter.addWidget(self.left_menu)

		# Строки левого меню: 0 — общие настройки, 1 — пустой спейсер,
		# с 2 — папки (catalog)
		main_settings_item = UListWidgetItem(
			parent=self.left_menu,
			text=Lng.general
		)
		main_settings_item.setIcon(QIcon(str(Static.COLOR_ICONS / "settings.svg")))
		self.left_menu.addItem(main_settings_item)

		spacer = UListSpacerItem(self.left_menu)
		self.left_menu.addItem(spacer)

		for i in Mf.items:
			new_folder = UListWidgetItem(self.left_menu, text=i.mf_alias)
			new_folder.setIcon(QIcon(str(Static.COLOR_ICONS / "image_folder.svg")))
			self.left_menu.addItem(new_folder)

		self.right_wid = TransparentWidget()
		self.right_lay = QVBoxLayout(self.right_wid)
		self.right_lay.setContentsMargins(0, 0, 0, 0)
		self.right_lay.setSpacing(0)
		self.right_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
		self.splitter.addWidget(self.right_wid)
		self.splitter.setStretchFactor(0, 0)
		self.splitter.setStretchFactor(1, 1)
		self.splitter.setSizes([200, 600])

		idx = 0
		if settings_item.type_ == "edit_folder":
			for x, i in enumerate(Mf.items, start=2):
				if i.mf_alias == self.settings_item.content:
					idx = x
					break
		elif settings_item.type_ == "new_folder":
			QTimer.singleShot(10, self.open_new_catalog_win)

		self.current_idx = idx
		self.left_menu.setCurrentRow(idx)
		self.init_right_side(idx)

	def open_new_catalog_win(self):
		self.new_catalog_win = NewMfSettings(mf_path=self.settings_item.content)
		self.new_catalog_win.center_to_parent(self)
		self.new_catalog_win.show()

	def init_right_side(self, idx: int):
		if idx == 0:
			r_wid = GeneralSettings()
		else:
			item: UListWidgetItem = self.left_menu.item(idx)
			for index, mf in enumerate(Mf.items):
				if mf.mf_alias == item.text():
					r_wid = MfSettings(index)
					self.settings_item.type_ = "general"
					self.settings_item.content = ""
					break

		# Любое изменение на странице помечает окно как несохранённое
		r_wid.changed.connect(self._on_page_changed)
		self.current_page = r_wid
		self.right_lay.insertWidget(0, r_wid)

	def _on_page_changed(self):
		self.has_unsaved = True
		self.save_widget.show_warning()

	def clear_right_side(self):
		wids = (GeneralSettings, MfSettings)
		right_wid = self.right_wid.findChild(wids)
		if right_wid is not None:
			right_wid.deleteLater()
		self.current_page = None

	def left_menu_click(self, *args):
		new_idx = self.left_menu.currentRow()
		if new_idx == self.current_idx:
			return

		if self.has_unsaved:
			self.pending_idx = new_idx
			self._ask_discard_for_switch()
			return

		self._switch_page(new_idx)

	def _switch_page(self, idx: int):
		self.clear_right_side()
		self.has_unsaved = False
		self.save_widget.hide_warning()
		self.left_menu.blockSignals(True)
		self.left_menu.setCurrentRow(idx)
		self.left_menu.blockSignals(False)
		self.current_idx = idx
		self.init_right_side(idx)

	def _restore_selection(self):
		# Возвращаем выделение на открытую страницу без повторного вызова left_menu_click
		self.left_menu.blockSignals(True)
		self.left_menu.setCurrentRow(self.current_idx)
		self.left_menu.blockSignals(False)

	def _ask_discard_for_switch(self):
		win = self._create_unsaved_window()
		win.ok_clicked.connect(self._on_switch_confirmed)
		win.cancel_clicked.connect(self._on_switch_cancelled)
		self._show_unsaved_window(win)

	def _ask_discard_for_close(self):
		win = self._create_unsaved_window()
		win.ok_clicked.connect(self._on_close_confirmed)
		self._show_unsaved_window(win)

	def _create_unsaved_window(self) -> ConfirmWindow:
		win = CancelChangesWin(Lng.unsaved_changes_confirm)
		return win

	def _show_unsaved_window(self, win: ConfirmWindow):
		win.center_to_parent(self)
		win.show()
		self.discard_win = win  # держим ссылку, чтобы окно не удалилось

	def _on_switch_confirmed(self):
		self.has_unsaved = False
		self._switch_page(self.pending_idx)

	def _on_switch_cancelled(self):
		self._restore_selection()

	def _on_close_confirmed(self):
		self.has_unsaved = False
		self.close()

	def save_settings_cmd(self):
		if not self.has_unsaved:
			self.deleteLater()
			return
		if self.current_page is not None:
			self.current_page.save_changes()

	def close(self) -> bool:
		if self.has_unsaved:
			self._ask_discard_for_close()
			return False
		return super().close()

	def deleteLater(self):
		if self.has_unsaved:
			self._ask_discard_for_close()
			return
		self.closed.emit()
		return super().deleteLater()

	def closeEvent(self, a0):
		if self.has_unsaved:
			a0.ignore()
			self._ask_discard_for_close()
			return
		self.closed.emit()
		return super().closeEvent(a0)

	def keyPressEvent(self, a0):
		if a0.key() == Qt.Key.Key_Escape:
			self.close()
			return
		return super().keyPressEvent(a0)