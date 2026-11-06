import os

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout

from cfg import Dynamic, JsonData, Static
from system.lang import Lng
from system.main_folder import Mf
from system.scaner import ScanProgress
from system.shared_utils import ImgUtils

from ._base_widgets import (GrayTextLabel, TransparentWidget, USep,
                            USlider)


# =============================================================================
# ПУТЬ (бывший bar_path.py)
# =============================================================================

class PathItem(TransparentWidget):
	new_history_item = pyqtSignal(str)
	load_st_grid = pyqtSignal()
	arrow_right = " \U0000203A"  # ›
	info_win = pyqtSignal(list)
	add_fav = pyqtSignal(str)
	del_fav = pyqtSignal(str)
	type_to_pixmap: dict = {}

	def __init__(self, dir: str, name: str):
		super().__init__()
		self.item_dir = dir

		item_layout = QHBoxLayout(self)
		item_layout.setContentsMargins(0, 0, 0, 0)
		item_layout.setSpacing(5)

		self.img_wid = QSvgWidget(str(Static.COLOR_ICONS / "base_folder.svg"))
		self.img_wid.setFixedSize(12, 12)
		item_layout.addWidget(self.img_wid)

		self.text_wid = GrayTextLabel(text=name)
		self.text_wid.set_font_size(11)
		self.collapse()
		item_layout.addWidget(self.text_wid)

	def add_arrow(self):
		t = self.text_wid.text() + " " + PathItem.arrow_right
		self.text_wid.setText(t)

	def del_arrow(self):
		t = self.text_wid.text().replace(PathItem.arrow_right, "")
		self.text_wid.setText(t)

	def expand(self):
		self.text_wid.setFixedWidth(self.text_wid.sizeHint().width())

	def collapse(self, min_w=5):
		if not self.text_wid.underMouse():
			self.text_wid.setMinimumWidth(min_w)


class PathBar(TransparentWidget):
	new_history_item = pyqtSignal(str)
	load_st_grid = pyqtSignal()
	info_win = pyqtSignal(list)
	add_fav = pyqtSignal(str)
	del_fav = pyqtSignal(str)

	def __init__(self):
		super().__init__()
		self.current_path: str = None

		self.h_layout = QHBoxLayout(self)
		self.h_layout.setSpacing(5)
		self.h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

	def update(self, dir: str, last_item_limit=40):
		"""
		Отобразить новый путь сетки / папки / файла
		src: путь сетки / папки / файла
		"""
		if dir == self.current_path:
			return
		for i in self.findChildren(PathItem):
			i.deleteLater()
		self.current_path = dir
		root = dir.strip(os.sep).split(os.sep)
		path_items: dict[int, PathItem] = {}

		for x, name in enumerate(root, start=1):
			item_dir = os.path.join(os.sep, *root[:x])
			path_item = PathItem(item_dir, name)
			path_item.new_history_item.connect(self.new_history_item.emit)
			path_item.load_st_grid.connect(self.load_st_grid.emit)
			path_item.info_win.connect(lambda lst: self.info_win.emit(lst))
			path_item.add_fav.connect(self.add_fav.emit)
			path_item.del_fav.connect(self.del_fav.emit)
			path_item.add_arrow()
			path_items[x] = path_item
			self.h_layout.addWidget(path_item)

		path_items[1].img_wid.load(
			str(Static.COLOR_ICONS / "image_folder.svg")
		)

		last_item = path_items.get(len(root))
		if dir.endswith(ImgUtils.ext_all):
			last_item.img_wid.load(
				str(Static.GRAY_ICONS / "image_icon_gray.svg")
			)

		text_ = last_item.text_wid.text()
		if len(text_) > last_item_limit:
			last_item.setFixedWidth(400)
			last_item.text_wid.set_elide(True)

		if len(root) != 1:
			last_item.del_arrow()


# =============================================================================
# ПРОГРЕСС (ProgressWidget)
# =============================================================================

class ProgressWidget(GrayTextLabel):
	qss_property_name = "style"
	qss_yellow = "yellow"
	qss_green = "green"
	qss_transparent = "transparent"

	def __init__(self):
		super().__init__("")
		self.set_font_size(11)
		self.setMidLineWidth(100)
		self.setMaximumWidth(250)
		self.set_elide(True, ignore_width=False)
		self.total_seconds = JsonData.scaner_minutes * 60
		self.timer = QTimer(self)
		self.timer.timeout.connect(self._on_tick)
		self._apply(self.qss_transparent)

	# --- Единая точка смены стиля и текста ---

	def _apply(self, qss_style: str, text: str = ""):
		self.setProperty(self.qss_property_name, qss_style)
		self.style().unpolish(self)
		self.style().polish(self)
		self.setText(text)
		self.update()

	# --- Публичный интерфейс для WinMain ---

	def show_status(self, progress: ScanProgress):
		"""Прогресс сканера. Таймер останавливается, чтобы не перебивать текст."""
		self.timer.stop()
		self._apply(self._status_style(progress), self.scan_progress_text(progress))

	def show_loading(self):
		"""Запуск сканера до первого прогресса."""
		self.timer.stop()
		self._apply(self.qss_transparent, Lng.loading)

	def show_timer(self):
		"""Обратный отсчёт до следующего сканирования."""
		self.total_seconds = JsonData.scaner_minutes * 60
		self._apply(self.qss_transparent, self._timer_text())
		self.timer.start(1000)

	def reset(self):
		"""Пустое состояние без таймера."""
		self.timer.stop()
		self._apply(self.qss_transparent)

	# --- Внутреннее ---

	def _status_style(self, progress: ScanProgress) -> str:
		if progress.kind == "indexing":
			return self.qss_green
		# поиск папок и отсутствие подключения выделяем жёлтым
		if progress.kind in ("search_dirs", "no_connection"):
			return self.qss_yellow
		return self.qss_transparent

	def _on_tick(self):
		self.total_seconds -= 1
		if self.total_seconds <= 0:
			self.timer.stop()
			return
		self.setText(self._timer_text())

	def _timer_text(self) -> str:
		minutes = self.total_seconds // 60
		seconds = self.total_seconds % 60
		return f"{Lng.next_search} {minutes:02d}:{seconds:02d}"

	def scan_progress_text(self, progress: ScanProgress) -> str:
		"""Текст прогресса сканера. Строится только в GUI-потоке, где доступен Lng."""
		if progress.kind == "search_dirs":
			return f"{progress.mf_alias}: {Lng.search_in.lower()}"
		if progress.kind == "indexing":
			return (
				f"{progress.mf_alias}: "
				f"{Lng.indexing_files.lower()} "
				f"{progress.current} {Lng.from_} {progress.total}"
			)
		return f"{progress.mf_alias}: {Lng.no_connection.lower()}"

	# --- Отладка: все демо-шаги внутри одного метода ---

	def run_demo(self, step_ms: int = 1500):
		"""
		Отладка: последовательно показывает все состояния и тексты разной длины
		(проверка смены стилей и elide), в конце запускает обратный отсчёт.
		Удаляется целиком этим методом.
		"""
		demo_texts = (
			"mf: ищу папки",
			"mf: индексация файлов 12 из 340",
			(
				"очень длинное имя хранилища для проверки elide: "
				"индексация файлов 12345 из 987654 и ещё очень много текста"
			),
		)
		styles = (self.qss_transparent, self.qss_yellow, self.qss_green)

		self.timer.stop()
		steps = [
			lambda s=style, t=text: self._apply(s, t)
			for text in demo_texts
			for style in styles
		]
		for i, step in enumerate(steps):
			QTimer.singleShot(i * step_ms, step)
		QTimer.singleShot(len(steps) * step_ms, self.show_timer)


# =============================================================================
# СЛАЙДЕР
# =============================================================================

class BarBottomSlider(USlider):
	def __init__(self):
		super().__init__()

	def _on_value_changed(self, value):
		Dynamic.current_pixmap_size_index = value
		super()._on_value_changed(value)


# =============================================================================
# ЕДИНЫЙ НИЖНИЙ БЛОК: путь сверху, прогресс и слайдер снизу
# =============================================================================

class BarBottom(TransparentWidget):
	resize_thumbnails = pyqtSignal()

	FOOTER_MARGINS = 5

	def __init__(self):
		super().__init__()

		# --- Вертикальный лэйаут: путь сверху, нижняя строка снизу ---
		self.v_layout = QVBoxLayout(self)
		self.v_layout.setContentsMargins(self.FOOTER_MARGINS, 5, self.FOOTER_MARGINS, 0)
		self.v_layout.setSpacing(0)

		# --- Путь ---
		self.bar_path = PathBar()
		self.bar_path.h_layout.setContentsMargins(0, 0, 0, 0)
		self.v_layout.addWidget(self.bar_path)

		self.v_layout.addSpacing(5)
		self.v_layout.addWidget(USep())

		# --- Нижняя строка: прогресс, выделение, слайдер ---
		bottom = TransparentWidget()
		self.h_layout = QHBoxLayout(bottom)
		self.h_layout.setContentsMargins(0, 0, 0, 0)
		self.h_layout.setSpacing(0)
		self.h_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
		self.v_layout.addWidget(bottom)

		# --- Прогресс ---
		self.progress_widget = ProgressWidget()
		self.h_layout.addWidget(self.progress_widget)

		# --- Подпись выделения строго по центру ---
		self.h_layout.addStretch(1)
		self.selection_label = GrayTextLabel("")
		self.selection_label.set_font_size(11)
		self.h_layout.addWidget(self.selection_label)
		self.h_layout.addStretch(1)

		# --- Слайдер справа ---
		self.slider = BarBottomSlider()
		self.slider.setOrientation(Qt.Orientation.Horizontal)
		self.slider.setMinimum(0)
		self.slider.setMaximum(len(Static.THUMB_WIDTHS) - 1)
		self.slider.setValue(Dynamic.current_pixmap_size_index)
		self.slider.setFixedWidth(80)
		self.slider.clicked.connect(self.resize_thumbnails)
		self.h_layout.addWidget(self.slider)

		self.progress_widget.raise_()

	def _objects_word(self, n: int) -> str:
		if JsonData.lng_index == 0:  # русский: три формы по правилам склонения
			n_abs = abs(n) % 100
			n1 = n_abs % 10
			if 11 <= n_abs <= 14:
				return Lng.selected_objects_many
			if n1 == 1:
				return Lng.selected_objects_one
			if 2 <= n1 <= 4:
				return Lng.selected_objects_few
			return Lng.selected_objects_many
		# английский: одна форма для 1, остальные во множественном
		return Lng.selected_objects_one if n == 1 else Lng.selected_objects_few

	def set_selection_count(self, n: int):
		if n <= 0:
			self.selection_label.setText("")
			return
		prefix = Lng.selected_prefix
		self.selection_label.setText(f"{prefix} {n} {self._objects_word(n)}")