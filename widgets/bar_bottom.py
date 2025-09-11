from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent, QWheelEvent
from PyQt5.QtWidgets import QLabel, QSlider, QWidget

from cfg import Dynamic, ThumbData

from ._base_widgets import UHBoxLayout


class CustomSlider(QSlider):
    """
    Кастомный горизонтальный слайдер для выбора размера миниатюр с сигналами
    и стилизованным внешним видом.

    Атрибуты:
        resize_thumbnails (pyqtSignal): сигнал для изменения размера миниатюр.
    """

    resize_thumbnails = pyqtSignal()

    def __init__(self):
        super().__init__()

        # --- Настройка диапазона и ориентации ---
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setMinimum(0)
        self.setMaximum(len(ThumbData.PIXMAP_SIZE) - 1)
        self.setValue(Dynamic.thumb_size_index)
        self.setFixedWidth(80)

        # --- Стилизация слайдера ---
        style = """
            QSlider::groove:horizontal {
                border-radius: 1px;
                height: 3px;
                margin: 0px;
                background-color: rgba(111, 111, 111, 0.5);
            }
            QSlider::handle:horizontal {
                background-color: rgba(199, 199, 199, 1);
                height: 10px;
                width: 10px;
                border-radius: 5px;
                margin: -4px 0;
                padding: -4px 0px;
            }
        """
        self.setStyleSheet(style)

        # --- Подключаем обработку изменения значения ---
        self.valueChanged.connect(self._on_value_changed)

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        """Устанавливает значение слайдера при клике мышью по шкале."""
        if ev.button() != Qt.LeftButton:
            ev.ignore()
            return

        ratio = ev.x() / self.width()
        value = self.minimum() + round(ratio * (self.maximum() - self.minimum()))
        self.setValue(value)
        ev.accept()
        super().mousePressEvent(ev)

    def wheelEvent(self, e: QWheelEvent | None) -> None:
        """Отключает изменение значения колесиком мыши."""
        if e:
            e.ignore()

    def _on_value_changed(self, value: int):
        """Обновляет текущий индекс миниатюр и эмитит сигнал resize_thumbnails."""
        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)

        Dynamic.thumb_size_index = value
        self.resize_thumbnails.emit()


class BarBottom(QWidget):
    """
    Нижняя панель с прогресс-баром и слайдером для изменения размера миниатюр.

    Сигналы:
        resize_thumbnails (pyqtSignal): испускается при изменении размера миниатюр.
    """

    resize_thumbnails = pyqtSignal()
    hh = 28

    def __init__(self):
        super().__init__()

        # --- Настройка размеров панели ---
        self.setFixedHeight(self.hh)

        # --- Горизонтальный layout ---
        self.h_layout = UHBoxLayout(self)
        self.h_layout.setSpacing(20)
        self.h_layout.setContentsMargins(0, 0, 15, 0)

        # --- Прогресс-бар ---
        self.progress_bar = QLabel(text="")
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # self.progress_bar.setFixedSize(300, 20)
        self.progress_bar.setFixedHeight(20)
        self.h_layout.addWidget(self.progress_bar)

        # --- Разделитель перед слайдером ---
        self.h_layout.addStretch()

        # --- Слайдер изменения размера миниатюр ---
        self.slider = CustomSlider()
        self.slider.resize_thumbnails.connect(self.resize_thumbnails)
        self.h_layout.addWidget(self.slider)
