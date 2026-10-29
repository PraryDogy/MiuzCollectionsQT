import os

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QButtonGroup, QGraphicsOpacityEffect, QHBoxLayout,
                             QToolButton)

from cfg import Dynamic, JsonData, Static
from system.lang import Lng

from ._base_widgets import (GrayTextLabel, SvgWithThemeBg, TransparentWidget,
                            UMenu, UPushButton, USlider)


class BarBottomSlider(USlider):
	def __init__(self):
		super().__init__()

	def _on_value_changed(self, value):
		Dynamic.current_pixmap_size_index = value
		super()._on_value_changed(value)


class BarBottomLeftLabel(GrayTextLabel):
	interval_ms = 1000  # 1 секунда
	ww = 250

	def __init__(self):
		super().__init__("")
		self.set_font_size(11)
		self.set_elide(True)
		self.setFixedWidth(self.ww)
		self.total_seconds = JsonData.scaner_minutes * 60
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.update_timer_text)

	def start_timer_text(self):

		self.timer.stop()
		self.total_seconds = JsonData.scaner_minutes * 60
		self.update_label()
		self.timer.start(self.interval_ms)

	def stop_timer_text(self):
		self.timer.stop()
		effect = QGraphicsOpacityEffect(self)
		effect.setOpacity(1.0)
		self.setGraphicsEffect(effect)

	def update_timer_text(self):
		self.total_seconds -= 1
		if self.total_seconds <= 0:
			self.timer.stop()
			return

		self.update_label()

	def update_label(self):
		minutes = self.total_seconds // 60
		seconds = self.total_seconds % 60

		text = (
			f"{Lng.next_search[JsonData.lng_index]} "
			f"{minutes:02d}:{seconds:02d}"
		)
		self.setText(text)


class BarBottom(TransparentWidget):
	resize_thumbnails = pyqtSignal()
	icon_path = Static.COMMON_ICONS / "next.svg"
	icon_size = 15

	def __init__(self):
		super().__init__()

		# --- Горизонтальный layout ---
		self.h_layout = QHBoxLayout(self)
		self.h_layout.setSpacing(0)
		self.h_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

		self.svg_wid = QSvgWidget()
		self.svg_wid.load(str(self.icon_path))
		self.svg_wid.setFixedSize(self.icon_size, self.icon_size)
		self.h_layout.addWidget(self.svg_wid)

		self.h_layout.addSpacing(5)

		# --- Прогресс-бар ---
		self.progress_bar = BarBottomLeftLabel()
		self.progress_bar.setText("")
		self.h_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignVCenter)

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
		idx = JsonData.lng_index
		if idx == 0:  # русский: три формы по правилам склонения
			n_abs = abs(n) % 100
			n1 = n_abs % 10
			if 11 <= n_abs <= 14:
				return Lng.selected_objects_many[idx]
			if n1 == 1:
				return Lng.selected_objects_one[idx]
			if 2 <= n1 <= 4:
				return Lng.selected_objects_few[idx]
			return Lng.selected_objects_many[idx]
		# английский: одна форма для 1, остальные во множественном
		return Lng.selected_objects_one[idx] if n == 1 else Lng.selected_objects_few[idx]

	def set_selection_count(self, n: int):
		if n <= 0:
			self.selection_label.setText("")
			return
		prefix = Lng.selected_prefix[JsonData.lng_index]
		self.selection_label.setText(f"{prefix} {n} {self._objects_word(n)}")