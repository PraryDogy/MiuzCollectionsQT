import os

from PyQt5.QtCore import QPoint, Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent, QWheelEvent
from PyQt5.QtWidgets import QAction, QFrame, QLabel, QSlider, QWidget

from ._base_widgets import UMenu, UHBoxLayout, SvgBtn
from cfg import Dynamic, Static, ThumbData
from system.lang import Lang
from signals import SignalsApp

from .actions import MenuTypes
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

DOWNLOADS_SVG = os.path.join(Static.images_dir, "downloads.svg")
SETTINGS_SVG = os.path.join(Static.images_dir, "settings.svg")


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
    resize_thumbnails = pyqtSignal()

    def __init__(self):
        super().__init__(
            orientation=Qt.Orientation.Horizontal,
            minimum=0,
            maximum=len(ThumbData.PIXMAP_SIZE) - 1
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


class FilterBtn(QLabel):
    obj_name = "filter_btn"
    reload_thumbnails = pyqtSignal()
    update_bottom_bar = pyqtSignal()

    def __init__(self):
        """
        Сигналы:
        - reload_thumbnails()
        # - update_bottom_bar()
        """

        t = f"{Lang.type_show}: {Lang.type_jpg}, {Lang.type_tiff}"
        super().__init__(text=t)
        self.setObjectName("filter_btn")
        # self.setFixedWidth(150)
        self.set_normal_style()

        self.adjustSize()

    def set_normal_style(self):
        self.setStyleSheet(f"#{FilterBtn.obj_name} {{{Static.border_transparent_style}}}")

    def set_solid_style(self):
        self.setStyleSheet(f"#{FilterBtn.obj_name} {{{Static.blue_bg_style}}}")

    def menu_types(self, *args):
        self.set_solid_style()

        menu_ = MenuTypes(parent=self)
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
        
        self.set_normal_style()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.menu_types()


class SvgBtn_(QFrame):
    def __init__(self, icon_path, size, parent = None):
        super().__init__(parent)

        v_lay = UHBoxLayout()
        self.setLayout(v_lay)
        self.layout().setContentsMargins(2, 1, 2, 1)
        self.svg_btn = SvgBtn(icon_path, size, parent)
        self.layout().addWidget(self.svg_btn)
        self.setStyleSheet(self.normal_style())
        self.adjustSize()

    def solid_style(self):
        style = f"""
        background: {Static.gray_color};
        border-radius: 6px;
        """
        return style

    def normal_style(self):
        style = f"""
        background: transparent;
        """
        return style

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

        self.downloads_win = None
        SignalsApp.instance.win_downloads_open.connect(self.open_downloads_win)
        SignalsApp.instance.win_downloads_close.connect(self.close_downloads_win)

    def init_ui(self):

        self.filter_label = FilterBtn()
        self.filter_label.reload_thumbnails.connect(lambda: self.reload_thumbnails.emit())
        self.filter_label.update_bottom_bar.connect(lambda: self.toggle_types())
        self.h_layout.addWidget(self.filter_label)

        self.h_layout.addStretch()

        self.progress_bar = QLabel(text="")
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.h_layout.addWidget(
            self.progress_bar,
            alignment=Qt.AlignmentFlag.AlignVCenter
        )

        self.downloads = SvgBtn_(icon_path=DOWNLOADS_SVG , size=20)
        self.downloads.mouseReleaseEvent = self.open_downloads_cmd
        self.h_layout.addWidget(self.downloads)

        self.sett_widget = SvgBtn_(SETTINGS_SVG, size=20)
        self.sett_widget.mouseReleaseEvent = self.sett_btn_cmd
        self.h_layout.addWidget(self.sett_widget)

        self.slider = CustomSlider()
        self.slider.resize_thumbnails.connect(lambda: self.resize_thumbnails.emit())
        self.h_layout.addWidget(self.slider)

    def toggle_types(self):
        types = []

        if Static.ext_non_layers in Dynamic.types:
            types.append(Lang.type_jpg)

        if Static.ext_layers in Dynamic.types:
            types.append(Lang.type_tiff)

        if not types:
            types = [
                Lang.type_jpg,
                Lang.type_tiff
            ]

        types = ", ".join(types)
        t = f"{Lang.type_show}: {types}"
        self.filter_label.setText(t)
        self.filter_label.adjustSize()

    def open_downloads_cmd(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.open_downloads_win()

    def open_downloads_win(self):
        if self.downloads_win is None:
            self.downloads_win = WinDownloads()
            self.downloads_win.closed.connect(self.downloads_win_closed)
            self.downloads_win.center_relative_parent(self.window())
            self.downloads_win.show()

    def downloads_win_closed(self, *args):
        self.downloads_win = None

    def close_downloads_win(self):
        try:
            self.downloads_win.deleteLater()
        except Exception:
            ...
        self.downloads_win = None

    def sett_btn_cmd(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.settings = WinSettings()
            self.settings.center_relative_parent(self.window())
            self.settings.theme_changed.connect(self.theme_changed.emit)
            self.settings.show()
    