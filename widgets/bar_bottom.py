import os

from PyQt5.QtCore import QPoint, Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent, QWheelEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QLabel, QSlider, QWidget

from cfg import Dynamic, Cfg, Static, ThumbData
from system.lang import Lng

from ._base_widgets import SvgBtn, UHBoxLayout
from .actions import MenuTypes
from .win_settings import WinSettings


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


class FilterBtn(QSvgWidget):
    obj_name = "filter_btn"
    reload_thumbnails = pyqtSignal()
    update_bottom_bar = pyqtSignal()

    def __init__(self):
        """
        Сигналы:
        - reload_thumbnails()
        # - update_bottom_bar()
        """

        t = f"{Lng.show[Cfg.lng]}: {Lng.type_jpg[Cfg.lng]}, {Lng.type_tiff[Cfg.lng]}"
        super().__init__()
        self.load("./images/filters.svg")
        self.setFixedSize(18, 18)

    def menu_types(self, *args):
        menu_ = MenuTypes(parent=self)
        menu_.setFixedWidth(130)
        menu_.reload_thumbnails.connect(lambda: self.reload_thumbnails.emit())
        menu_.update_bottom_bar.connect(lambda: self.update_bottom_bar.emit())

        widget_rect = self.rect()
        menu_size = menu_.sizeHint()

        centered = QPoint(
            menu_size.width() // 2,
            menu_size.height() + self.height() // 2
        )

        menu_center_top = self.mapToGlobal(widget_rect.center()) - centered

        menu_.move(menu_center_top)
        menu_.exec_()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.menu_types()


class BarBottom(QWidget):
    theme_changed = pyqtSignal()
    reload_thumbnails = pyqtSignal()
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
        
        # from PyQt5.QtCore import QTimer
        # t = "длинное имя папки: обновление (1000)"
        # QTimer.singleShot(1000, lambda: self.progress_bar.setText(t))

        self.filter_label = FilterBtn()
        self.filter_label.reload_thumbnails.connect(lambda: self.reload_thumbnails.emit())
        self.filter_label.update_bottom_bar.connect(lambda: self.toggle_types())
        self.h_layout.addWidget(self.filter_label)

        self.sett_widget = QSvgWidget()
        self.sett_widget.load("./images/settings.svg")
        self.sett_widget.setFixedSize(20, 20)
        self.sett_widget.mouseReleaseEvent = self.sett_btn_cmd
        self.h_layout.addWidget(self.sett_widget)

        self.slider = CustomSlider()
        self.slider.resize_thumbnails.connect(lambda: self.resize_thumbnails.emit())
        self.h_layout.addWidget(self.slider)

    def toggle_types(self):
        types = []

        if Static.ext_non_layers in Dynamic.types:
            types.append(Lng.type_jpg[Cfg.lng])

        if Static.ext_layers in Dynamic.types:
            types.append(Lng.type_tiff[Cfg.lng])

        if not types:
            types = [
                Lng.type_jpg[Cfg.lng],
                Lng.type_tiff[Cfg.lng]
            ]

        types = ", ".join(types)
        t = f"{Lng.show[Cfg.lng]}: {types}"
        self.filter_label.setText(t)
        self.filter_label.adjustSize()

    def sett_btn_cmd(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.win_settings = WinSettings()
            self.win_settings.center_relative_parent(self.window())
            self.win_settings.show()
    