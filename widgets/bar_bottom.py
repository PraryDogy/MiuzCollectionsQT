import os

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout

from cfg import Dynamic, JsonData, Static
from system.items import Mf
from system.lang import Lng
from system.scaner import ScanProgress
from system.utils import ImageReader

from ._base_widgets import GrayTextLabel, TransparentWidget, USep, USlider

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

	def update_path(self, dir: str, last_item_limit=40):
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
		if dir.endswith(ImageReader.ext_all):
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

class ProgressWidget(TransparentWidget):
	set_warning = pyqtSignal()
	set_green_checkmark = pyqtSignal()
	set_arrow_terminal = pyqtSignal()
	path_visible_changed = pyqtSignal(bool)  # True, когда показан путь

	def __init__(self):
		super().__init__()
		self._last_alias: str | None = None
		self._last_text: str | None = None

		# Путь показывается полностью, без обрезки
		self.alias_label = GrayTextLabel("")
		self.alias_label.set_font_size(11)

		# Статус идёт сразу за путём
		self.status_label = GrayTextLabel("")
		self.status_label.set_font_size(11)

		self.h_layout = QHBoxLayout(self)
		self.h_layout.setContentsMargins(0, 0, 0, 0)
		self.h_layout.setSpacing(0)
		self.h_layout.addWidget(self.alias_label)
		self.h_layout.addWidget(self.status_label)
		self.h_layout.addStretch()

		self.total_seconds = JsonData.scaner_minutes * 60
		self.timer = QTimer(self)
		self.timer.timeout.connect(self._on_tick)
		self.reset()

	# --- Публичный интерфейс для WinMain ---

	def show_status(self, progress: ScanProgress):
		"""Прогресс сканера. Таймер останавливается, чтобы не перебивать текст."""
		self.timer.stop()
		alias, text = self.scan_progress_parts(progress)
		self._set_texts(alias, text)
		if progress.kind == "indexing":
			self.set_green_checkmark.emit()
		elif progress.kind in ("no_connection",):
			self.set_warning.emit()
		else:
			self.set_arrow_terminal.emit()

	def show_loading(self):
		"""Запуск сканера до первого прогресса."""
		self.timer.stop()
		self._set_texts("", Lng.loading)
		self.set_arrow_terminal.emit()

	def show_timer(self):
		"""Обратный отсчёт до следующего сканирования."""
		self.total_seconds = JsonData.scaner_minutes * 60
		self._set_texts("", self._timer_text())
		self.set_arrow_terminal.emit()
		self.timer.start(1000)

	def reset(self):
		"""Пустое состояние без таймера."""
		self.timer.stop()
		self._set_texts("", "")
		self.set_arrow_terminal.emit()

	# --- Внутреннее ---

	def _set_texts(self, alias: str, text: str):
		if alias == self._last_alias and text == self._last_text:
			return
		self._last_alias = alias
		self._last_text = text

		self.alias_label.setText(alias)
		self.alias_label.setVisible(bool(alias))
		self.status_label.setText(text)
		self.path_visible_changed.emit(bool(alias))
		QTimer.singleShot(50, lambda: self.alias_label.setToolTip(alias[:-1]))

	def _on_tick(self):
		self.total_seconds -= 1
		if self.total_seconds <= 0:
			self.timer.stop()
			return
		self.status_label.setText(self._timer_text())

	def _timer_text(self) -> str:
		minutes = self.total_seconds // 60
		seconds = self.total_seconds % 60
		return f"{Lng.next_search} {minutes:02d}:{seconds:02d}"

	def scan_progress_parts(self, progress: ScanProgress) -> tuple[str, str]:
		"""Подпись слева и текст статуса отдельно. Строится только в GUI-потоке, где доступен Lng."""
		if progress.kind == "search_dirs":
			return f"{progress.mf_alias}: ", Lng.search_in.lower()
		if progress.kind == "indexing":
			return f"{self._short_dir(progress.dir_path)}: ", (
				f"{Lng.indexing_files.lower()} "
				f"{progress.current} {Lng.from_} {progress.total}"
			)
		return f"{progress.mf_alias}: ", Lng.no_connection.lower()

	# --- Отладка: демо состояний и elide ---

	def run_demo(self, step_ms: int = 15500):
		"""
		Отладка: короткий и длинный алиас с одинаковым статусом, в конце запускает таймер.
		Удаляется целиком этим методом.
		"""
		status = "индексация файлов 12 из 340"
		demo_steps = [
			# (self.set_green_checkmark, "mf:", status),
			(self.set_green_checkmark, "очень длинное имя хранилища для проверки elide:", status),
		]
		self.timer.stop()
		for i, (signal, alias, text) in enumerate(demo_steps):
			QTimer.singleShot(
				i * step_ms,
				lambda s=signal, a=alias, t=text: (s.emit(), self._set_texts(a, t)),
			)
		QTimer.singleShot(len(demo_steps) * step_ms, self.show_timer)

	@staticmethod
	def _short_dir(path: str, max_parts: int = 15) -> str:
		"""/Users/me/Downloads/Folder 1/images folder -> /…/Folder 1/images folder"""
		parts = [p for p in path.split(os.sep) if p]
		if len(parts) <= max_parts:
			return os.sep + os.sep.join(parts)
		return os.sep + "…" + os.sep + os.sep.join(parts[-max_parts:])


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

		self.progress_svg = QSvgWidget(str(Static.GRAY_ICONS / "arrow_terminal_gray.svg"))
		self.progress_svg.setFixedSize(12, 12)
		self.h_layout.addWidget(self.progress_svg)

		self.h_layout.addSpacing(5)

		# --- Прогресс: растягивается, когда выделение скрыто ---
		self.progress_widget = ProgressWidget()
		self.progress_widget.set_arrow_terminal.connect(
			lambda: self.progress_svg.load(str(Static.GRAY_ICONS / "arrow_terminal_gray.svg"))
		)
		self.progress_widget.set_warning.connect(
			lambda: self.progress_svg.load(str(Static.COLOR_ICONS / "yellow_warning.svg"))
		)
		self.progress_widget.set_green_checkmark.connect(
			lambda: self.progress_svg.load(str(Static.COLOR_ICONS / "green_checkmark.svg"))
		)
		self.h_layout.addWidget(self.progress_widget)

		self.h_layout.addStretch()

		# --- Слайдер справа ---
		self.slider = BarBottomSlider()
		self.slider.setOrientation(Qt.Orientation.Horizontal)
		self.slider.setMinimum(0)
		self.slider.setMaximum(len(Static.THUMB_WIDTHS) - 1)
		self.slider.setValue(Dynamic.current_pixmap_size_index)
		self.slider.setFixedWidth(80)
		self.slider.clicked.connect(self.resize_thumbnails)
		self.h_layout.addWidget(self.slider)

		# QTimer.singleShot(1000, self.progress_widget.run_demo)
