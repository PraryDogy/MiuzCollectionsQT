from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent, QWheelEvent
from PyQt5.QtWidgets import QLabel, QSlider, QWidget

from cfg import Dynamic, ThumbData

from ._base_widgets import UHBoxLayout


class BaseSlider(QSlider):
    _clicked = pyqtSignal()

    def __init__(self, orientation: Qt.Orientation, min_: int, max_: int):
        super().__init__()
        self.setOrientation(orientation)
        self.setMinimum(min_)
        self.setMaximum(max_)

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

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        if ev.button() != Qt.LeftButton:
            ev.ignore()
            return

        ratio = ev.x() / self.width()
        value = self.minimum() + round(ratio * (self.maximum() - self.minimum()))
        self.setValue(value)
        ev.accept()
        super().mousePressEvent(ev)

    def wheelEvent(self, e: QWheelEvent | None) -> None:
        e.ignore()


class CustomSlider(BaseSlider):
    resize_thumbnails = pyqtSignal()

    def __init__(self):
        super().__init__(
            orientation=Qt.Orientation.Horizontal,
            min_=0,
            max_=len(ThumbData.PIXMAP_SIZE) - 1
        )
        self.setFixedWidth(80)
        self.setValue(Dynamic.thumb_size_ind)

        self.valueChanged.connect(self.move_)
    
    def move_(self, value: int):
        # Отключаем сигнал valueChanged
        self.blockSignals(True)
        self.setValue(value)
        # Включаем сигнал обратно
        self.blockSignals(False)
        Dynamic.thumb_size_ind = value
        self.resize_thumbnails.emit()


class BarBottom(QWidget):
    resize_thumbnails = pyqtSignal()

    def __init__(self):
        """
        Сигналы:
        - reload_thumbnails()
        - theme_changed()
        """
        super().__init__()

        self.setFixedHeight(28)

        self.h_layout = UHBoxLayout(self)
        self.h_layout.setSpacing(20)
        self.h_layout.setContentsMargins(0, 0, 15, 0)
        self.init_ui()

    def init_ui(self):
        self.progress_bar = QLabel(text="")
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.setFixedHeight(20)
        self.h_layout.addWidget(self.progress_bar)

        self.h_layout.addStretch()

        self.slider = CustomSlider()
        self.slider.resize_thumbnails.connect(lambda: self.resize_thumbnails.emit())
        self.h_layout.addWidget(self.slider)
