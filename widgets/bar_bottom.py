import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent, QWheelEvent
from PyQt5.QtWidgets import (QApplication, QFrame, QLabel, QSlider,
                             QSpacerItem, QWidget)

from base_widgets import CustomProgressBar, LayoutH, SvgBtn
from cfg import cnf
from signals import signals_app
from styles import Names, Themes
from utils.main_utils import MainUtils

from .win_downloads import DownloadsWin
from .win_settings import WinSettings


class ProgressBar(QWidget):
    def __init__(self):
        super().__init__()

        layout = LayoutH(self)

        self.title = QLabel()
        layout.addWidget(self.title)

        spacer = QSpacerItem(10, 0)
        layout.addItem(spacer)

        self.progress_bar = CustomProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        signals_app.progressbar_value.connect(self.progressbar_value)

    def progressbar_value(self, value: int):

        if not isinstance(value, int):
            raise Exception ("widgets > bar_bottom > progress bar > set_value > value not int", value)

        self.progress_bar.setValue(value)

        if self.progress_bar.value() == 100:
            self.progress_bar.hide()
        else:
            self.progress_bar.show()

        
class BaseSlider(QSlider):
    _clicked = pyqtSignal()

    def __init__(self, orientation: Qt.Orientation, minimum: int, maximum: int):
        super().__init__(orientation=orientation, minimum=minimum, maximum=maximum)

        st = f"""
            QSlider::groove:horizontal {{
                border-radius: 1px;
                height: 3px;
                margin: 0px;
                background-color: rgba(111, 111, 111, 0.5);
            }}
            QSlider::handle:horizontal {{
                background-color: rgba(199, 199, 199, 1);
                height: 10px;
                width: 10px;
                border-radius: 5px;
                margin: -4px 0;
                padding: -4px 0px;
            }}
            """

        self.setStyleSheet(st)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(ev)
        else:
            ev.ignore()

    def wheelEvent(self, e: QWheelEvent | None) -> None:
        e.ignore()


class CustomSlider(BaseSlider):

    def __init__(self):
        super().__init__(orientation=Qt.Orientation.Horizontal, minimum=0, maximum=3)
        self.setFixedWidth(80)
        self.setValue(cnf.curr_size_ind)
        self.valueChanged.connect(self.change_size)
        signals_app.move_slider.connect(self.move_slider_cmd)
    
    def move_slider_cmd(self, value: int):
        self.setValue(value)
        cnf.curr_size_ind = value
        signals_app.resize_grid.emit()

    def change_size(self, value: int):
        self.setValue(value)
        cnf.curr_size_ind = value
        signals_app.resize_grid.emit()


class BarBottom(QFrame):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(28)
        self.setObjectName(Names.st_bar_frame)
        self.setStyleSheet(Themes.current)
        
        self.h_layout = LayoutH(self)
        self.h_layout.setSpacing(20)
        self.h_layout.setContentsMargins(15, 0, 15, 0)
        self.init_ui()
        
        signals_app.reload_stbar.connect(self.reload_stbar)

    def init_ui(self):
        self.h_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.progress_bar = ProgressBar()
        self.progress_bar.setFixedWidth(120)
        self.h_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignRight)

        self.downloads = SvgBtn(icon_path=os.path.join("images", f"{cnf.theme}_downloads.svg") , size=20)
        self.downloads.mouseReleaseEvent = self.open_downloads
        signals_app.hide_downloads.connect(self.downloads.hide)
        signals_app.show_downloads.connect(self.downloads.show)
        self.h_layout.addWidget(self.downloads, alignment=Qt.AlignmentFlag.AlignRight)

        self.switch_theme = SvgBtn(icon_path=os.path.join("images", f"{cnf.theme}_switch.svg"), size=20)
        self.switch_theme.mouseReleaseEvent = self.switch_theme_cmd
        self.h_layout.addWidget(self.switch_theme, alignment=Qt.AlignmentFlag.AlignRight)

        self.sett_widget = SvgBtn(icon_path=os.path.join("images", f"{cnf.theme}_settings.svg"), size=20)
        self.sett_widget.mouseReleaseEvent = self.sett_btn_cmd
        self.h_layout.addWidget(self.sett_widget, alignment=Qt.AlignmentFlag.AlignRight)

        self.custom_slider = CustomSlider()
        self.h_layout.addWidget(self.custom_slider, alignment=Qt.AlignmentFlag.AlignRight)

        self.downloads.hide()

    def reload(self):
        signals_app.reload_thumbnails.emit()
        signals_app.reload_menu.emit()
        signals_app.reload_filters_bar.emit()
        signals_app.reload_stbar.emit()

    def reload_stbar(self):
        MainUtils.clear_layout(self.h_layout)
        self.init_ui()

    def switch_theme_cmd(self, e):
        all_widgets = QApplication.allWidgets()
        widgets = [
            widget
            for widget in all_widgets
            if widget.objectName()
            ]
                
        if cnf.theme == "dark_theme":
            Themes.set_theme("light_theme")
            cnf.theme = "light_theme"

        else:
            Themes.set_theme("dark_theme")
            cnf.theme = "dark_theme"

        for i in widgets:
            i.setStyleSheet(Themes.current)

        self.sett_widget.set_icon(os.path.join("images", f"{cnf.theme}_settings.svg"))
        self.downloads.set_icon(os.path.join("images", f"{cnf.theme}_downloads.svg"))
        self.switch_theme.set_icon(os.path.join("images", f"{cnf.theme}_switch.svg"))

        cnf.write_json_cfg()

    def open_downloads(self, e):
        self.downloads_win = DownloadsWin(parent=self)
        self.downloads_win.center_win(self)
        self.downloads_win.show()

    def sett_btn_cmd(self, e):
        self.settings = WinSettings(parent=self)
        self.settings.show()

    def switch_view_cmd(self, e):
        cnf.small_view = not cnf.small_view
        signals_app.reload_thumbnails.emit()
        self.switch_view.switch_icon()
        cnf.write_json_cfg()
