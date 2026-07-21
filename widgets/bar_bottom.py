import os

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QGraphicsOpacityEffect, QHBoxLayout, QLabel,
                             QWidget)

from cfg import Cfg, Dynamic, Static
from system.lang import Lng

from ._base_widgets import GrayLabel, USlider


class ThumbnailsSlider(USlider):
    def __init__(self):
        super().__init__()

    def _on_value_changed(self, value):
        Dynamic.thumb_size_index = value
        super()._on_value_changed(value)


class ProgressWidget(GrayLabel):
    interval_ms = 1000  # 1 секунда

    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_text_size(11)

        self.total_seconds = Cfg.scaner_minutes * 60

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer_text)

    def start_timer_text(self):

        self.timer.stop()
        self.total_seconds = Cfg.scaner_minutes * 60
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
            f"{Lng.next_search[Cfg.lng_index]} "
            f"{minutes:02d}:{seconds:02d}"
        )
        self.setText(text)


class BarBottom(QWidget):
    resize_thumbnails = pyqtSignal()
    icon_path = os.path.join(Static.internal_images, "next.svg")
    icon_size = 12

    def __init__(self):
        super().__init__()

        # --- Горизонтальный layout ---
        self.h_layout = QHBoxLayout(self)
        self.h_layout.setSpacing(5)
        self.h_layout.setContentsMargins(0, 0, 15, 0)
        self.h_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.svg_wid = QSvgWidget()
        self.svg_wid.load(self.icon_path)
        self.svg_wid.setFixedSize(self.icon_size, self.icon_size)
        self.h_layout.addWidget(self.svg_wid)

        # --- Прогресс-бар ---
        self.progress_bar = ProgressWidget()
        self.progress_bar.setFixedHeight(self.icon_size)
        self.progress_bar.setText("")
        self.progress_bar.setFixedHeight(self.icon_size)
        self.h_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignVCenter)

        # --- Разделитель перед слайдером ---
        self.h_layout.addStretch()

        # --- Слайдер изменения размера миниатюр ---
        self.slider = ThumbnailsSlider()

        self.slider.setOrientation(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(Static.pixmap_sizes) - 1)
        self.slider.setValue(Dynamic.thumb_size_index)
        self.slider.setFixedWidth(80)

        self.slider.clicked.connect(self.resize_thumbnails)
        self.h_layout.addWidget(self.slider)
