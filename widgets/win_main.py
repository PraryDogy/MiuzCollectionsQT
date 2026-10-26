import functools
import os
import subprocess

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QGuiApplication, QKeyEvent, QImage
from PyQt6.QtWidgets import QSizePolicy, QSplitter, QVBoxLayout

from cfg import Dynamic, JsonData, Static
from system.filters import Filters
from system.items import DataItem, SettingsItem
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import (FilesRemover, ProcessWorker, UpdateThumb,
                                 UpdateThumbItem)
from system.scaner import (BaseScaner, ForcedScaner, ForcedScanerItem,
                           ScanerWorker)
from system.shared_utils import ImgUtils
from system.tasks import SetFav, UThreadPool, Utils

from ._base_widgets import (ConfirmWindow, TransparentLabel, TransparentWidget,
                            UGroupBox, UMainWindow, USep, WarningWindow)
from .bar_bottom import BarBottom
from .bar_macos import BarMacos
from .bar_path import PathBar
from .bar_top import BarTop
from .grid import Grid, GridStandart, Thumb
from .menu_left import MenuLeft
from .win_collage import WinCollage
from .win_copy_files import WinCopyFiles
from .win_filters import WinFilters
from .win_image_view import ImgViewItem, WinImageView
from .win_img_search import WinImgSearch
from .win_info import WinInfo
from .win_servers import ServersWin
from .win_settings import WinSettings
from .win_smb import WinSmb
from .win_upload import UploadWin

# =============================================================================
# БИЗНЕС-ЛОГИКА (без зависимостей от виджетов Qt)
# =============================================================================

SUPPORTED_EXT_LOWER = tuple(ext.lower() for ext in ImgUtils.ext_all)


def to_abs_paths(mf_current_path: str, rel_paths) -> list[str]:
	"""Относительные пути грида -> абсолютные пути на диске."""
	return [Utils.add_mf_path(mf_current_path, i) for i in rel_paths]


def destination_dir(mf_current_path: str, current_dir: str) -> str:
	"""Каталог, куда вставляются файлы из буфера."""
	return os.path.join(mf_current_path, current_dir.strip(os.sep))


def dirs_to_rescan(abs_paths) -> set[str]:
	"""Каталоги, которые нужно пересканировать после изменения файлов."""
	return {os.path.dirname(p) for p in abs_paths}


def remove_confirm_key(files_count: int) -> str:
	"""Ключ текста подтверждения удаления в Lng."""
	return "remove_file_question" if files_count == 1 else "remove_files_question"


def filter_supported(paths) -> list[str]:
	"""Оставляет файлы с поддерживаемыми расширениями (без учёта регистра)."""
	return [p for p in paths if p.lower().endswith(SUPPORTED_EXT_LOWER)]


def view_selection(selected: list, all_items: list) -> tuple[list, bool]:
	"""Что листать в просмотрщике: одиночный выбор -> вся сетка, иначе только выбранное.
	Возвращает (элементы, is_selection). selected должен быть не пуст."""
	if len(selected) == 1:
		return all_items, False
	return selected, True


def next_size_index(current: int, sizes_count: int, step: int) -> int:
	"""Новый индекс размера миниатюр с ограничением по краям. step: +1 или -1."""
	return max(0, min(current + step, sizes_count - 1))


def db_changed(previous_mtime: int, current_mtime: int) -> bool:
	"""Нужно ли перезагрузить сетку и дерево после сканирования."""
	return previous_mtime != current_mtime


def reset_mf_after_rejection(mf) -> None:
	"""Пользователь отказался от найденных опасных файлов: сбрасываем хранилище в корень."""
	mf.set_mf_current_path(None)
	mf.mf_paths = [""]


class ForcedDirsRegistry:
	"""Каталоги, которые нужно пересканировать принудительно."""

	def __init__(self):
		self._dirs: set[str] = set()

	def add(self, *dirs: str) -> None:
		self._dirs.update(dirs)

	def take(self) -> set[str]:
		"""Забирает накопленные каталоги и очищает реестр."""
		dirs = self._dirs.copy()
		self._dirs.clear()
		return dirs

	def __bool__(self) -> bool:
		return bool(self._dirs)


# =============================================================================
# UI
# =============================================================================

class TestWid(TransparentLabel):
	def __init__(self, parent=None):
		super().__init__(parent=parent, text="TEST")
		self.setFixedHeight(50)
		self.setAlignment(Qt.AlignmentFlag.AlignCenter)

	def reload(self):
		from ._base_widgets import ConfirmWindow
		self.confirm_win = ConfirmWindow(
			text="Стандратное окно подтверждения, другая строка и другой текстовый текст"
		)
		self.confirm_win.center_to_parent(self.window())
		self.confirm_win.show()

	def mouseReleaseEvent(self, a0):
		self.reload()
		return super().mouseReleaseEvent(a0)


class DangerWarn(ConfirmWindow):
	icon_path = Static.COMMON_ICONS / "red_warning.svg"

	def __init__(self, mf_alias: str, removed_images_count: int):
		text = (
			f"{Lng.dangerous_text[JsonData.lng_index]}".format(removed_images_count)
		)
		super().__init__(text)
		self.svg_widget.load(str(self.icon_path))
		self.ok_btn.setText(Lng.allow[JsonData.lng_index])
		self.cancel_btn.setText(Lng.deny[JsonData.lng_index])

	def closeEvent(self, a0):
		a0.ignore()

	def keyPressEvent(self, a0):
		return


class WinMain(UMainWindow):
	min_w = 750
	left_side_width = 250
	ww, hh = 1200, 800
	FOOTER_MARGINS = 5

	def __init__(self, argv: list):
		super().__init__()
		# отступы от окна слева справа, кроме заголовка окна
		self.central_layout.setContentsMargins(5, 0, 5, 0)
		self.central_layout.setSpacing(0)
		self.setMinimumWidth(self.min_w)
		self.setMenuBar(BarMacos())

		# self.test = DangerWarn(Mf.current_mf.mf_alias, 35)
		# self.test.center_to_parent(self)
		# self.test.show()

		# test_wid = TestWid()
		# self.central_layout.addWidget(test_wid)

		self.forced_scaner_dirs = ForcedDirsRegistry()
		self.go_to_url: str | None = None
		self.files_to_copy = set()
		self.stop_scaner = True

		self.bar_top = BarTop()
		# отступ справа в заголовке окна
		self.bar_top.h_layout.setContentsMargins(0, 0, 10, 0)
		self.title_bar.set_custom_widget(self.bar_top)
		self.set_titlebar_height(self.bar_top.height() + 8)

		self.bar_top.open_settings_win.connect(
			lambda settings_item: self.open_settings_win(settings_item)
		)
		self.bar_top.open_img_search_win.connect(
			lambda: self.open_img_search_win()
		)
		self.bar_top.start_text_search.connect(
			lambda: self.base_search_start()
		)
		self.bar_top.mf_new.connect(
			lambda settings_item: self.open_settings_win(settings_item)
		)
		self.bar_top.mf_open.connect(
			lambda mf: self.on_mf_clicked(mf)
		)

		# Создаем QSplitter
		self.splitter = QSplitter(Qt.Orientation.Horizontal)
		self.splitter.setHandleWidth(15)
		self.splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
		self.central_layout.addWidget(self.splitter)

		self.left_menu = MenuLeft()
		self.left_menu.reveal.connect(
			lambda rel_paths: self.reveal_in_finder(rel_paths)
		)
		self.left_menu.on_tree_clicked.connect(
			lambda abs_path: self.on_tree_clicked(abs_path)
		)
		self.left_menu.on_mf_clicked.connect(
			lambda mf: self.on_mf_clicked(mf)
		)
		self.left_menu.on_hide_digits_clicked.connect(
			lambda: self.on_hide_digits_clicked()
		)
		self.left_menu.copy_path.connect(
			lambda rel_paths: self.copy_path(rel_paths)
		)
		self.splitter.addWidget(self.left_menu)

		# Правый виджет
		right_wid = UGroupBox()
		self.splitter.addWidget(right_wid)
		self.right_layout = QVBoxLayout(right_wid)
		self.right_layout.setContentsMargins(0, 10, 0, 10)
		self.right_layout.setSpacing(0)

		self.grid = Grid()
		self.load_st_grid()

		self.splitter.setStretchFactor(0, 0)
		self.splitter.setStretchFactor(1, 1)
		self.resize(self.ww, self.hh)

		# --- Создаем единый контейнер для всего нижнего блока ---
		self.footer_container = TransparentWidget()
		self.footer_layout = QVBoxLayout(self.footer_container)
		
		# слева справа доп отступы, чтобы быть уже, чем основные виджеты
		# сетка и левое меню, отступ сверху от сетки и меню
		self.footer_layout.setContentsMargins(self.FOOTER_MARGINS, 5, self.FOOTER_MARGINS, 0)
		self.footer_layout.setSpacing(0)

		self.bar_path = PathBar()
		self.bar_path.h_layout.setContentsMargins(0, 0, 0, 0)
		self.path_bar_update("")
		self.footer_layout.addWidget(self.bar_path)

		self.footer_layout.addSpacing(5)

		# 2. Добавляем горизонтальный разделитель
		bar_bottom_sep = USep()
		self.footer_layout.addWidget(bar_bottom_sep)

		# левый и правый маргин для красивого отступа
		self.bar_bottom = BarBottom()
		self.bar_bottom.h_layout.setContentsMargins(0, 0, 0, 0)
		self.bar_bottom.resize_thumbnails.connect(
			lambda: self.grid.resize_thumbnails()
		)
		self.footer_layout.addWidget(self.bar_bottom)

		# --- Добавляем уже готовый собранный виджет в главный лэйаут ---
		self.central_layout.addWidget(self.footer_container)

		if "noscan" not in argv:
			self.start_scaner_task()
		else:
			print("СКАНЕР ВЫКЛЮЧЕН")
			self.bar_bottom.progress_bar.setText("noscan enabled")

		# QTimer.singleShot(100, lambda: self.open_win_smb(Mf.current_mf))

	@staticmethod
	def with_conn(fn: callable):
		@functools.wraps(fn)
		def wrapper(self: "WinMain", *args):
			avaiable_mf_path = Mf.current_mf.get_avaiable_mf_path()
			if avaiable_mf_path:
				Mf.current_mf.set_mf_current_path(avaiable_mf_path)
				return fn(self, *args)
			self.open_win_smb(Mf.current_mf)
			return None
		return wrapper

	def set_no_img_search(self):
		Dynamic.img_search_thumb_paths.clear()
		self.bar_top.img_search_btn.set_base_style()
		try:
			self.win_img_search.deleteLater()
		except (RuntimeError, AttributeError):
			...

	def base_search_start(self):
		self.left_menu.tree_wid.expand_to_path(os.sep)
		self.load_st_grid()

	def open_img_search_win(self):
		def on_closed():
			win = self.win_img_search
			if not win.preview_widget.pixmap.isNull():
				self.bar_top.img_search_btn.set_selected_style()
				win.hide()
			else:
				self.bar_top.img_search_btn.set_base_style()
				self.win_img_search = None
				win.deleteLater()

		self.bar_top.img_search_btn.set_selected_style()

		if not getattr(self, "win_img_search", None):
			self.win_img_search = WinImgSearch()
			self.win_img_search.reload_thumbnails.connect(self.load_st_grid)
			self.win_img_search.closed.connect(on_closed)
			self.win_img_search.center_to_parent(self)

		self.win_img_search.show()
		self.win_img_search.raise_()
		self.win_img_search.activateWindow()
	
	def show_in_app(self, rel_path: str):
		current_dir = os.path.dirname(rel_path)
		Dynamic.current_dir = current_dir
		self.go_to_url = rel_path
		self.load_st_grid()
		self.left_menu.tree_wid.expand_to_path(current_dir)
	
	def path_bar_update(self, path: str):
		dir = f"/{Mf.current_mf.mf_alias}{path}"
		self.bar_path.update(dir)

	def on_hide_digits_clicked(self):
		self.win_warn = WarningWindow(Lng.hide_digits_full[JsonData.lng_index])
		self.win_warn.ok_clicked.connect(self.win_warn.deleteLater)
		self.win_warn.center_to_parent(self)
		self.win_warn.show()
		
	def open_filters_win(self):

		def edit_filters():
			settings_item = SettingsItem("filters", "")
			self.open_settings_win(settings_item)

		self.filters_win = WinFilters()
		self.filters_win.load_st_grid.connect(self.load_st_grid)
		self.filters_win.edit_filters.connect(edit_filters)
		self.filters_win.center_to_parent(self.window())
		self.filters_win.show()

	def open_win_smb(self, mf: Mf):
		self.win_smb = WinSmb(mf)
		self.win_smb.center_to_parent(self.win_list[-2])
		self.win_smb.show()

	def on_mf_clicked(self, mf: Mf):
		Mf.current_mf = mf
		Dynamic.current_dir = os.sep
		self.path_bar_update(Dynamic.current_dir)
		self.left_menu.tree_wid.abs_selected_path = os.sep
		self.left_menu.tree_wid.init_ui()
		self.load_st_grid()

		mf_path = mf.get_avaiable_mf_path()
		if not mf_path:
			self.open_win_smb(mf)
 
	@with_conn
	def on_tree_clicked(self, abs_path: str):
		rel_path = Utils.remove_mf_path(
			mf_path=Mf.current_mf.mf_current_path,
			abs_path=abs_path
		)
		Dynamic.current_dir = rel_path
		self.load_st_grid()
		self.path_bar_update(Dynamic.current_dir)

	@with_conn
	def start_update_thumb(self, rel_paths: list[str]):

		def poll_task():
			queue = self.update_thumb_task.process_queue
			while not queue.empty():
				update_thumb_item: UpdateThumbItem = queue.get()
				wid = self.grid.url_to_wid.get(update_thumb_item.rel_img_path)
				if wid:
					base_qimage = Utils.qimage_from_array(update_thumb_item.array)
					resized_qimages = []
					if JsonData.square_thumbs:
						scaled_fn = Utils.scale_qimage_square
					else:
						scaled_fn = Utils.scale_qimage_dpr
					for i in Static.THUMB_WIDTHS:
						x = scaled_fn(base_qimage, i)
						resized_qimages.append(x)
					wid.data_item.base_qimage = base_qimage
					wid.data_item.resized_qimages = resized_qimages
					wid.set_pixmap_with_actual_size()
  
			if not self.update_thumb_task.is_alive():
				self.update_thumb_task.terminate_join()
			else:
				QTimer.singleShot(700, poll_task)

		rel_set = set(rel_paths)
		for url, wid in self.grid.url_to_wid.items():
			if url in rel_set:
				wid.img_wid.show_updating()

		self.update_thumb_task = ProcessWorker(
			target=UpdateThumb.start,
			args=(Mf.current_mf, rel_paths, )
		)
		self.update_thumb_task.start()
		QTimer.singleShot(300, poll_task)

	@with_conn
	def save_to_downloads(self, rel_paths: list[str]):
		downloads = os.path.expanduser("~/Downloads")
		abs_paths = [
			Utils.add_mf_path(Mf.current_mf.mf_current_path, i)
			for i in rel_paths
		]
		copy_files_win = self.copy_files_win(
			files_to_copy=abs_paths,
			dest=downloads
		)
		copy_files_win.finished_.connect(
			Utils.macos_reveal_files
		)

	@with_conn
	def set_files_to_copy(self, rel_paths: tuple):
		abs_files_to_copy = set(
			Utils.add_mf_path(Mf.current_mf.mf_current_path, i)
			for i in rel_paths
		)

		self.files_to_copy = abs_files_to_copy
		self.grid.files_to_copy = abs_files_to_copy

	@with_conn
	def paste_files(self, files_to_copy: list[str], dest: str):
		"""
		files_to_copy, dest
		"""
		# копия списка: буфер очищается ниже, а окно копирования читает его позже
		copy_files_win = self.copy_files_win(
			files_to_copy=list(files_to_copy),
			dest=dest
		)
		copy_files_win.finished_.connect(lambda *_: self.start_scaner_task())
		self.forced_scaner_dirs.add(dest)
		self.files_to_copy.clear()
		self.grid.files_to_copy.clear()

	@with_conn
	def open_in_app(self, rel_paths: list[str], app_path: str):
		for i in rel_paths:
			abs_path = Utils.add_mf_path(Mf.current_mf.mf_current_path, i)
			if app_path:
				subprocess.Popen(["open", "-a", app_path, abs_path])
			else:
				subprocess.Popen(["open", abs_path])

	@with_conn
	def reveal_in_finder(self, rel_paths: list):
		abs_paths = to_abs_paths(Mf.current_mf.mf_current_path, rel_paths)
		if not abs_paths:
			return
		if os.path.isdir(abs_paths[0]):
			subprocess.Popen(["open", abs_paths[0]])
		else:
			Utils.macos_reveal_files(abs_paths)

	@with_conn
	def copy_path(self, rel_paths: list[str]):
		abs_paths = [
			Utils.add_mf_path(Mf.current_mf.mf_current_path, i)
			for i in rel_paths
		]
		Utils.pyqt_copy_text("\n".join(abs_paths))

	@with_conn
	def remove_files(self, rel_paths: list, ms = 300):
		
		def poll_file_remover():
			if not file_remover.process_queue.empty():
				file_remover.process_queue.get()
			if not file_remover.is_alive():
				file_remover.terminate_join()
				for i in dirs_to_scan:
					self.forced_scaner_dirs.add(i)

				self.start_scaner_task()
			else:
				QTimer.singleShot(ms, poll_file_remover)

		def start_file_remover():
			file_remover.start()
			QTimer.singleShot(ms, poll_file_remover)

		abs_paths = to_abs_paths(Mf.current_mf.mf_current_path, rel_paths)
		if not abs_paths:
			return
		dirs_to_scan = dirs_to_rescan(abs_paths)
		text = getattr(Lng, remove_confirm_key(len(abs_paths)))[JsonData.lng_index]
		self.remove_files_win = ConfirmWindow(text)
		file_remover = ProcessWorker(
				target=FilesRemover.start,
				args=(abs_paths, )
			)
		self.remove_files_win.center_to_parent(self.window())
		self.remove_files_win.ok_clicked.connect(start_file_remover)
		self.remove_files_win.show()
	
	@with_conn
	def upload_files(self, dropped_files: list[str]):

		def fin(dest: str):
			self.upload_win.deleteLater()
			self.paste_files(dropped_files, dest)


		dropped_files = filter_supported(dropped_files)
		self.upload_win = UploadWin(
			mf=Mf.current_mf,
			current_dir=Dynamic.current_dir,
			files_to_copy=dropped_files
		)
		self.upload_win.ok_clicked.connect(
			lambda dest: fin(dest)
		)
		self.upload_win.center_to_parent(self)
		self.upload_win.show()

	@with_conn
	def open_info_win(self, rel_paths: list[str]):
		
		abs_paths = [
			Utils.add_mf_path(Mf.current_mf.mf_current_path, i)
			for i in rel_paths
		]
		self.info_win = WinInfo(abs_paths)
		self.info_win.center_to_parent(UMainWindow.win_list[-2])
		self.info_win.show()

	def open_settings_win(self, settings_item: SettingsItem):
		self.bar_top.settings_btn.set_selected_style()
		self.settings_win = WinSettings(settings_item)
		self.settings_win.closed.connect(
			self.bar_top.settings_btn.set_base_style
		)
		self.settings_win.center_to_parent(self.window())
		self.settings_win.show()

	def load_st_grid(self, layout_index: int = 3):

		def finished():
			self.grid.setFocus()
			if self.go_to_url:
				target_url, self.go_to_url = self.go_to_url, str()
				widget = self.grid.url_to_wid.get(target_url)
				if not widget:
					return
				self.grid.select_by_url(target_url)
				QTimer.singleShot(
					100,
					lambda: self.grid.ensureWidgetVisible(widget)
				)

		self.bar_top.search_wid.update_placeholder()
		Dynamic.loaded_thumbs = 0
		self.grid.deleteLater()
		self.grid = GridStandart()
		self.grid.files_to_copy = self.files_to_copy
		self.grid.restart_scaner.connect(
			lambda: self.restart_scaner_task()
		)
		self.grid.remove_files.connect(
			lambda rel_paths: self.remove_files(rel_paths)
		)
		self.grid.open_img_view.connect(
			lambda: self.open_view_win(Mf.current_mf)
		)
		self.grid.save_files.connect(
			lambda rel_paths: self.save_to_downloads(rel_paths)
		)
		self.grid.open_info_win.connect(
			lambda rel_paths: self.open_info_win(rel_paths)
		)
		self.grid.copy_path.connect(
			lambda rel_paths: self.copy_path(rel_paths)
		)
		self.grid.reveal_in_finder.connect(
			lambda rel_paths: self.reveal_in_finder(rel_paths)
		)
		self.grid.set_fav.connect(
			lambda data: self.set_fav(data)
		)
		self.grid.open_in_app.connect(
			lambda data: self.open_in_app(*data)
		)
		# контекстное меню, берешь files_to_copy из буффера
		self.grid.paste_files.connect(
			lambda: self.paste_files(
				self.files_to_copy,
				destination_dir(Mf.current_mf.mf_current_path, Dynamic.current_dir)
			)
		)
		self.grid.set_files_to_copy.connect(
			lambda rel_paths: self.set_files_to_copy(rel_paths)
		)
		self.grid.setup_mf.connect(
			lambda item: self.open_settings_win(item)
		)
		self.grid.path_bar_update.connect(
			lambda rel_path: self.path_bar_update(rel_path)
		)
		self.grid.update_thumb.connect(
			lambda rel_paths: self.start_update_thumb(rel_paths)
		)
		self.grid.show_in_app.connect(
			self.show_in_app
		)
		self.grid.finished_.connect(
			finished
		)
		self.grid.load_st_grid.connect(
			self.load_st_grid
		)
		self.grid.upload_files.connect(
			lambda abs_paths: self.upload_files(abs_paths)
		)
		self.grid.collage.connect(
			lambda data_items: self.open_collage_win(data_items)
		)
		self.grid.open_filters_win.connect(
			lambda: self.open_filters_win()
		)
		self.right_layout.addWidget(self.grid)

	@with_conn
	def open_view_win(self, mf: Mf):
		if not self.grid.selected_widgets:
			return
		all_items = [i.data_item for i in self.grid.url_to_wid.values()]
		selected_items = [i.data_item for i in self.grid.selected_widgets]
		data_items, is_selection = view_selection(selected_items, all_items)
		start_data_item = selected_items[0]

		item = ImgViewItem(
			start_data_item=start_data_item,
			data_items=data_items,
			is_selection=is_selection
		)
		self.view_win = WinImageView(item)
		self.view_win.open_win_info.connect(
			lambda rel_paths: self.open_info_win(rel_paths)
		)
		self.view_win.copy_path.connect(
			lambda rel_paths: self.copy_path(rel_paths)
		)
		self.view_win.reveal_in_finder.connect(
			lambda rel_paths: self.reveal_in_finder(rel_paths)
		)
		self.view_win.set_fav.connect(
			self.set_fav
		)
		self.view_win.save_files.connect(
			lambda rel_paths: self.save_to_downloads(rel_paths)
		)
		self.view_win.select_thumb.connect(
			lambda path: self.grid.select_by_url(path)
		)
		self.view_win.open_in_app.connect(
			lambda data: self.open_in_app(*data)
		)
		self.view_win.image_not_exists.connect(
			lambda: self.open_win_smb(Mf.current_mf)
		)
		self.view_win.data_item_updated.connect(
			lambda data: self.update_thumb_image(data)
		)
		if WinImageView.xx == 0:
			self.view_win.resize(self.ww, self.hh)
			self.view_win.center_to_parent(self.window())
			self.view_win.move(self.view_win.x() + 10, self.view_win.y() + 10)
		else:
			self.view_win.resize(WinImageView.ww, WinImageView.hh)
			self.view_win.move(WinImageView.xx, WinImageView.yy)
		self.view_win.show()

	def update_thumb_image(self, rel_img_path: str):
		wid = self.grid.url_to_wid.get(rel_img_path)
		if wid:
			wid.set_pixmap_with_actual_size()

	def poll_scaner_task(self, ms: int = 3000):

		def can_continue(can_continue: bool, mf_alias: str):
			"""
			True = продолжить сканирование, False = прервать сканирование
			"""
			self.win_warn.deleteLater()
			self.scaner_task.response_queue.put(can_continue)
			if not can_continue:
				mf = next((m for m in Mf.items if m.mf_alias == mf_alias), None)
				if mf:
					reset_mf_after_rejection(mf)
					self.open_win_smb(mf)

		if not hasattr(self, "scaner_task") or not self.scaner_task:
			self.scaner_poll_timer.start(ms)
			return
		while not self.scaner_task.process_queue.empty():
			data = self.scaner_task.process_queue.get()

			if isinstance(data, tuple):
				mf_alias, removed_images_count = data
				self.win_warn = DangerWarn(mf_alias, removed_images_count)
				self.win_warn.center_to_parent(self)
				self.win_warn.ok_clicked.connect(lambda: can_continue(True, mf_alias))
				self.win_warn.cancel_clicked.connect(lambda: can_continue(False, mf_alias))
				self.win_warn.show()

			else:
				if self.bar_bottom.progress_bar.text() != data:
					self.bar_bottom.progress_bar.setText(data)

		if not self.scaner_task.is_alive():
			self.scaner_task.terminate_join()
			self.bar_bottom.progress_bar.setText("")
			self.bar_bottom.progress_bar.start_timer_text()
			new_db_time = int(os.stat(Static.DB_FILE).st_mtime)
			if db_changed(self.db_mtime, new_db_time):
				self.load_st_grid()
				self.left_menu.tree_wid.init_ui()
		else:
			self.scaner_poll_timer.start(ms)

	def start_scaner_task(self, ms: int = 3000):

		if not hasattr(self, "scaner_task"):
			# print("первая инициация сканера")
			self.scaner_task = None
			self.db_mtime = 0

			self.scaner_check_timer = QTimer(self)
			self.scaner_check_timer.setSingleShot(True)
			self.scaner_check_timer.timeout.connect(
				self.start_scaner_task
			)

			self.scaner_poll_timer = QTimer(self)
			self.scaner_poll_timer.setSingleShot(True)
			self.scaner_poll_timer.timeout.connect(
				self.poll_scaner_task
			)

		can_start = False
		alive = self.scaner_task.is_alive() if self.scaner_task else False

		# задача завершена
		if not alive:
			can_start = True

		if can_start:
			forced_dirs = self.forced_scaner_dirs.take()
			if forced_dirs:
				forced_scaner_item = ForcedScanerItem(
					mf=Mf.current_mf,
					dirs_to_scan=forced_dirs,
					lng_index=JsonData.lng_index
				)
				self.scaner_task = ScanerWorker(
					target=ForcedScaner.start,
					args=(forced_scaner_item, )
					)
			else:
				# print("штатно запускаю ОБЩИЙ сканер")
				self.scaner_task = ScanerWorker(
					target=BaseScaner.start,
					args=(Mf.items, JsonData.lng_index, )
				)
			self.db_mtime = int(os.stat(Static.DB_FILE).st_mtime)
			self.bar_bottom.progress_bar.stop_timer_text()
			self.bar_bottom.progress_bar.setText(Lng.loading[JsonData.lng_index])
			self.scaner_task.start()
			self.scaner_poll_timer.stop()
			self.scaner_poll_timer.start(ms)
			self.scaner_check_timer.stop()
			self.scaner_check_timer.start(JsonData.scaner_minutes * 60 * 1000)
		else:
			# проверяем каждую минуту, что задача завершена
			self.scaner_check_timer.stop()
			self.scaner_check_timer.start(5000)

	def restart_scaner_task(self):
		try:
			self.scaner_task.terminate_join()
		except AttributeError as e:
			print("Win main restart scaner task", e)
		self.start_scaner_task()
		
	def center_screen(self):
		# Получаем геометрию первичного (главного) экрана
		screen = QGuiApplication.primaryScreen().geometry()
		# Получаем геометрию текущего окна
		size = self.geometry()
		
		# Вычисляем координаты центра
		x = (screen.width() - size.width()) // 2
		y = (screen.height() - size.height()) // 2
		
		# Перемещаем окно
		self.move(x, y)

	def on_exit(self):
		try:
			if hasattr(self, "scaner_task"):
				self.scaner_task.terminate_join()
			ProcessWorker.stop_all()
		except Exception as e:
			print("on exit main win terminate error", e)
		JsonData.write_json_data()
		Filters.write_json_data()
		Mf.write_json_data()
		os._exit(0)

	def open_collage_win(self, data_items: list[DataItem]):
		self.collage_win = WinCollage(data_items)
		self.collage_win.center_to_parent(self)
		self.collage_win.show()

	def set_fav(self, data: tuple[str, int]):

		def finished(rel_path: str, value: int):
			self.grid.set_thumb_fav(rel_path, value)
			try:
				self.view_win.set_title()
			except AttributeError:
				...

		rel_path, value = data
		self.task = SetFav(rel_path, value)
		self.task.sigs.finished_.connect(
			lambda: finished(rel_path, value)
		)
		UThreadPool.start(self.task)

	def copy_files_win(self, files_to_copy: list[str], dest: str):
		progress_win = WinCopyFiles(
			files_to_copy=files_to_copy,
			target_dir=dest
		)
		progress_win.center_to_parent(self)
		progress_win.show()   
		return progress_win
	
	def open_server_win(self):
		self.server_win = ServersWin()
		self.server_win.center_to_parent(self)
		self.server_win.show()

	def closeEvent(self, a0: QCloseEvent | None) -> None:
		self.hide()
		a0.ignore()
	
	def keyPressEvent(self, a0: QKeyEvent | None) -> None:
		
		if a0.key() == Qt.Key.Key_V:
			if a0.modifiers() == Qt.KeyboardModifier.ControlModifier and self.files_to_copy:
				dest = destination_dir(Mf.current_mf.mf_current_path, Dynamic.current_dir)
				self.paste_files(self.files_to_copy, dest)

		elif a0.key() == Qt.Key.Key_W:
			if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
				self.hide()

		elif a0.key() == Qt.Key.Key_F:
			if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
				self.bar_top.search_wid.setFocus()

		elif a0.key() == Qt.Key.Key_K:
			if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
				self.open_server_win()

		elif a0.key() == Qt.Key.Key_Escape:
			if self.isFullScreen():
				self.showNormal()
				self.raise_()
			else:
				a0.ignore()

		elif a0.key() in (Qt.Key.Key_Equal, Qt.Key.Key_Minus):
			if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
				step = 1 if a0.key() == Qt.Key.Key_Equal else -1
				new_index = next_size_index(
					Dynamic.current_pixmap_size_index,
					len(Static.THUMB_WIDTHS),
					step
				)
				if new_index != Dynamic.current_pixmap_size_index:
					Dynamic.current_pixmap_size_index = new_index
					self.bar_bottom.slider._on_value_changed(new_index)
	
	def resizeEvent(self, a0):
		wid = self.splitter.widget(1)
		self.bar_path.setMaximumWidth(wid.width())
		return super().resizeEvent(a0)
