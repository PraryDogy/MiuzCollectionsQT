import os
from typing import Literal

from PyQt5.QtCore import QEvent, Qt, pyqtSignal
from PyQt5.QtGui import (QFontMetrics, QMouseEvent, QPainter, QPaintEvent,
                         QWheelEvent)
from PyQt5.QtWidgets import QApplication, QLabel, QSlider, QWidget

from base_widgets import LayoutHor, SvgBtn
from cfg import JsonData, Static
from signals import SignalsApp

from .win_downloads import WinDownloads
from .win_settings import WinSettings

SLIDER_STYLE = """
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

DOWNLOADS_SVG = os.path.join(Static.IMAGES, "downloads.svg")
SETTINGS_SVG = os.path.join(Static.IMAGES, "settings.svg")


class BaseSlider(QSlider):
    _clicked = pyqtSignal()

    def __init__(self, orientation: Qt.Orientation, minimum: int, maximum: int):
        super().__init__(
            orientation=orientation,
            minimum=minimum,
            maximum=maximum
        )
        self.setStyleSheet(SLIDER_STYLE)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(ev)
        else:
            ev.ignore()

    def wheelEvent(self, e: QWheelEvent | None) -> None:
        e.ignore()


class CustomSlider(BaseSlider):

    def __init__(self):
        super().__init__(
            orientation=Qt.Orientation.Horizontal,
            minimum=0,
            maximum=3
        )
        self.setFixedWidth(80)
        self.setValue(JsonData.curr_size_ind)

        self.valueChanged.connect(self.move_slider_cmd)
        SignalsApp.all_.slider_change_value.connect(self.move_slider_cmd)
    
    def move_slider_cmd(self, value: int):
        # Отключаем сигнал valueChanged
        self.blockSignals(True)
        self.setValue(value)
        # Включаем сигнал обратно
        self.blockSignals(False)
        JsonData.curr_size_ind = value
        SignalsApp.all_.grid_thumbnails_cmd.emit("resize")


class MyLabel(QLabel):
    def paintEvent(self, a0: QPaintEvent | None) -> None:
        painter = QPainter(self)

        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(
            self.text(),
            Qt.TextElideMode.ElideNone,
            self.width()
        )

        painter.drawText(self.rect(), self.alignment(), elided)
        return super().paintEvent(a0)


class BarBottom(QWidget):
    path_label: QLabel = None

    def __init__(self):
        super().__init__()

        self.setFixedHeight(28)

        self.h_layout = LayoutHor(self)
        self.h_layout.setSpacing(20)
        self.h_layout.setContentsMargins(15, 0, 15, 0)
        self.init_ui()

    def init_ui(self):
        path_label = MyLabel("")
        path_label.setMinimumWidth(1)
        self.h_layout.addWidget(
            path_label,
            alignment=Qt.AlignmentFlag.AlignLeft
        )
        BarBottom.path_label = path_label

        self.h_layout.addStretch()

        self.progress_bar = QLabel(text="")
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignRight)
        SignalsApp.all_.progressbar_text.connect(self.progress_bar.setText)
        self.h_layout.addWidget(
            self.progress_bar,
            alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        )

        self.downloads = SvgBtn(icon_path=DOWNLOADS_SVG , size=20)
        self.downloads.mouseReleaseEvent = self.open_downloads
        SignalsApp.all_.btn_downloads_toggle.connect(self.btn_downloads_toggle)
        self.h_layout.addWidget(
            self.downloads,
            alignment=Qt.AlignmentFlag.AlignRight
        )

        self.sett_widget = SvgBtn(SETTINGS_SVG, size=20)
        self.sett_widget.mouseReleaseEvent = self.sett_btn_cmd
        self.h_layout.addWidget(
            self.sett_widget,
            alignment=Qt.AlignmentFlag.AlignRight
        )

        self.custom_slider = CustomSlider()
        self.h_layout.addWidget(
            self.custom_slider,
            alignment=Qt.AlignmentFlag.AlignRight
        )

        self.downloads.hide()

    def btn_downloads_toggle(self, flag: Literal["hide", "show"]):
        if flag == "hide":
            self.downloads.hide()
        elif flag == "show":
            self.downloads.show()
        else:
            raise Exception("widgets >bar bottom > btn downloads > wrong flag", flag)

    def open_downloads(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.downloads_win = WinDownloads()
            self.downloads_win.center_relative_parent(self.window())
            self.downloads_win.show()

    def sett_btn_cmd(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.settings = WinSettings()
            self.settings.center_relative_parent(self.window())
            self.settings.show()
