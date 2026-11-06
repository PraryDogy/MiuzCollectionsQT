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
		self.set_elide(True)
		self.setFixedWidth(250)
		self.total_seconds = JsonData.scaner_minutes * 60
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.update_timer_text)
		self.set_qss_style(self.qss_transparent)

	def set_qss_style(self, qss_style: str):
		self.setProperty(ProgressWidget.qss_property_name, qss_style)
		self.style().unpolish(self)
		self.style().polish(self)
		self.update()

	def start_timer_text(self):
		self.timer.stop()
		self.total_seconds = JsonData.scaner_minutes * 60
		self.set_qss_style(self.qss_transparent)
		self.update_label()
		self.timer.start(1000)

	def stop_timer_text(self):
		self.timer.stop()
		self.set_qss_style(self.qss_transparent)

	def update_timer_text(self):
		self.total_seconds -= 1
		if self.total_seconds <= 0:
			self.timer.stop()
			return
		self.update_label()

	def update_label(self):
		minutes = self.total_seconds // 60
		seconds = self.total_seconds % 60
		self.setText(f"{Lng.next_search} {minutes:02d}:{seconds:02d}")

	def set_text(self, scan_progress: ScanProgress):
		if scan_progress.kind == "indexing":
			self.set_qss_style(self.qss_green)
		elif scan_progress.kind == "no_connection":
			self.set_qss_style(self.qss_yellow)
		else:
			self.set_qss_style(self.qss_transparent)

		self.setText(self.scan_progress_text(scan_progress))

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


class BarBottom(TransparentWidget):
	resize_thumbnails = pyqtSignal()

	def __init__(self):
		super().__init__()

		# --- Горизонтальный layout ---
		self.h_layout = QHBoxLayout(self)
		self.h_layout.setSpacing(0)
		self.h_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

		self.svg_wid = QSvgWidget(str(Static.GRAY_ICONS / "arrow_terminal_gray.svg"))
		self.svg_wid.setFixedSize(12, 12)
		self.h_layout.addWidget(self.svg_wid)

		self.h_layout.addSpacing(5)

		# --- Прогресс-бар ---
		self.progress_widget = ProgressWidget()
		self.progress_widget.setText("")
		self.progress_widget.set_qss_style(ProgressWidget.qss_transparent)
		self.h_layout.addWidget(self.progress_widget, alignment=Qt.AlignmentFlag.AlignVCenter)

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