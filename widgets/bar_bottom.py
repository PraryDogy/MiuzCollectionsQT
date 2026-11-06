import os

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QButtonGroup, QGraphicsOpacityEffect, QHBoxLayout,
                             QToolButton)

from cfg import Dynamic, JsonData, Static
from system.lang import Lng
from system.scaner import ScanProgress

from ._base_widgets import (GrayTextLabel, TransparentWidget, UMenu,
                            UPushButton, USlider)


class BarBottomSlider(USlider):
	def __init__(self):
		super().__init__()

	def _on_value_changed(self, value):
		Dynamic.current_pixmap_size_index = value
		super()._on_value_changed(value)


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


class BarBottom(TransparentWidget):
	resize_thumbnails = pyqtSignal()

	def __init__(self):
		super().__init__()

		# --- Горизонтальный layout ---
		self.h_layout = QHBoxLayout(self)
		self.h_layout.setSpacing(0)
		self.h_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

		# self.svg_wid = QSvgWidget(str(Static.GRAY_ICONS / "arrow_terminal_gray.svg"))
		# self.svg_wid.setFixedSize(12, 12)
		# self.h_layout.addWidget(self.svg_wid)

		# self.h_layout.addSpacing(5)

		# --- Прогресс-бар ---
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

		# QTimer.singleShot(500, self.progress_widget.run_demo)

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