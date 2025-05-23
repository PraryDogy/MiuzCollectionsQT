import os
from typing import Literal

from PyQt5.QtCore import QPoint, Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent, QWheelEvent
from PyQt5.QtWidgets import QAction, QLabel, QSlider, QWidget, QFrame

from base_widgets import ContextCustom, LayoutHor, SvgBtn
from cfg import Dynamic, Static, ThumbData
from lang import Lang
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
            maximum=len(ThumbData.PIXMAP_SIZE) - 1
        )
        self.setFixedWidth(80)
        self.setValue(Dynamic.thumb_size_ind)

        self.valueChanged.connect(self.move_slider_cmd)
        SignalsApp.instance.slider_change_value.connect(self.move_slider_cmd)
    
    def move_slider_cmd(self, value: int):
        # Отключаем сигнал valueChanged
        self.blockSignals(True)
        self.setValue(value)
        # Включаем сигнал обратно
        self.blockSignals(False)
        Dynamic.thumb_size_ind = value
        SignalsApp.instance.grid_thumbnails_cmd.emit("resize")


class FilterBtn(QLabel):
    obj_name = "filter_btn"

    def __init__(self):
        t = f"{Lang.type_show}: {Lang.type_jpg}, {Lang.type_tiff}"
        super().__init__(text=t)
        self.setObjectName("filter_btn")
        self.setFixedWidth(150)
        self.set_normal_style()

    def set_normal_style(self):
        self.setStyleSheet(f"#{FilterBtn.obj_name} {{{Static.NORMAL_STYLE}}}")

    def set_solid_style(self):
        self.setStyleSheet(f"#{FilterBtn.obj_name} {{{Static.SOLID_STYLE}}}")

    def set_border_style(self):
        self.setStyleSheet(f"#{FilterBtn.obj_name} {{{Static.BORDERED_STYLE}}}")

    def set_enter_style(self):
        self.setStyleSheet(f"#{FilterBtn.obj_name} {{{Static.SOLID_GRAY_STYLE}}}")

    def menu_types(self, *args):
        self.set_solid_style()

        menu_ = MenuTypes(parent=self)

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

    def enterEvent(self, a0):
        self.old_style = self.styleSheet()
        self.set_enter_style()
        return super().enterEvent(a0)
    
    def leaveEvent(self, a0):
        self.setStyleSheet(self.old_style)
        return super().leaveEvent(a0)

    def contextMenuEvent(self, ev):
        self.set_border_style()
        menu = ContextCustom(event=ev)

        view_action = QAction(parent=menu, text=Lang.view)
        view_action.triggered.connect(self.menu_types)
        menu.addAction(view_action)

        menu.show_menu()
        self.set_normal_style()
        
        return super().contextMenuEvent(ev)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.menu_types()


class SvgBtn_(QFrame):
    def __init__(self, icon_path, size, parent = None):
        super().__init__(parent)

        v_lay = LayoutHor()
        self.setLayout(v_lay)
        self.layout().setContentsMargins(2, 1, 2, 1)
        self.svg_btn = SvgBtn(icon_path, size, parent)
        self.layout().addWidget(self.svg_btn)
        self.setStyleSheet(self.normal_style())
        self.adjustSize()

    def solid_style(self):
        style = f"""
        background: {Static.RGB_GRAY};
        border-radius: 6px;
        """
        return style

    def normal_style(self):
        style = f"""
        background: transparent;
        """
        return style

    def enterEvent(self, a0):
        self.setStyleSheet(self.solid_style())
        return super().enterEvent(a0)

    def leaveEvent(self, a0):
        self.setStyleSheet(self.normal_style())
        return super().leaveEvent(a0)

class BarBottom(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedHeight(28)

        self.h_layout = LayoutHor(self)
        self.h_layout.setSpacing(20)
        self.h_layout.setContentsMargins(0, 0, 15, 0)
        self.init_ui()

        self.downloads_win = None
        SignalsApp.instance.bar_bottom_filters.connect(self.toggle_types)
        SignalsApp.instance.win_downloads_open.connect(self.open_downloads_win)
        SignalsApp.instance.win_downloads_close.connect(self.close_downloads_win)

    def init_ui(self):

        self.filter_label = FilterBtn()
        self.h_layout.addWidget(self.filter_label)

        self.h_layout.addStretch()

        self.progress_bar = QLabel(text="")
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignRight)
        SignalsApp.instance.progressbar_text.connect(self.progress_bar.setText)
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

        self.custom_slider = CustomSlider()
        self.h_layout.addWidget(self.custom_slider)

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
            self.downloads_win.close()
        except Exception:
            ...
        self.downloads_win = None

    def sett_btn_cmd(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.settings = WinSettings()
            self.settings.center_relative_parent(self.window())
            self.settings.show()
