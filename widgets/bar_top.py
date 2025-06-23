from typing import Literal

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QMouseEvent
from PyQt5.QtWidgets import QAction, QLabel, QWidget

from base_widgets import ContextCustom, LayoutHor
from cfg import Dynamic, JsonData, Static
from filters import Filter
from lang import Lang
from signals import SignalsApp

from .wid_search import WidSearch
from .win_dates import WinDates

BTN_W, BTN_H = 80, 28


class BarTopBtn(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.setFixedSize(BTN_W, BTN_H)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_solid_style(self):
        self.setStyleSheet(Static.blue_bg_style)

    def set_normal_style(self):
        self.setStyleSheet(Static.border_transparent_style)


class DatesBtn(BarTopBtn):
    open_dates_win = pyqtSignal()

    def __init__(self):
        super().__init__(text=Lang.dates)

    def open_win(self):
        self.open_dates_win.emit()

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.open_win()


class FilterBtn(BarTopBtn):
    def __init__(self, filter: Filter):
        super().__init__(text=filter.names[JsonData.lang_ind])

        self.filter = filter

        if filter.value:
            self.set_solid_style()
        else:
            self.set_normal_style()
        
    def toggle_cmd(self):
        self.filter.value = not self.filter.value

        if self.filter.value:
            self.set_solid_style()
        else:
            self.set_normal_style()

        SignalsApp.instance.grid_thumbnails_cmd.emit("reload")
        SignalsApp.instance.grid_thumbnails_cmd.emit("to_top")
    
    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        else:
            self.toggle_cmd()


class BarTop(QWidget):
    open_dates_win = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedHeight(35)
        self.h_layout = LayoutHor()
        self.setLayout(self.h_layout)
        self.filter_btns = []
        self.win_dates = None
        self.init_ui()

    def init_ui(self):
        self.filter_btns.clear()

        for filter in Filter.filters_list:
            label = FilterBtn(filter)
            self.filter_btns.append(label)
            self.h_layout.addWidget(
                label,
                alignment=Qt.AlignmentFlag.AlignLeft
            )
        
        self.dates_btn = DatesBtn()
        self.dates_btn.open_dates_win.connect(lambda: self.open_dates_win.emit())
        self.h_layout.addWidget(
            self.dates_btn,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.h_layout.addStretch(1)

        self.search_wid = WidSearch()
        self.h_layout.addWidget(
            self.search_wid,
            alignment=Qt.AlignmentFlag.AlignRight
        )

        if any((Dynamic.date_start, Dynamic.date_end)):
            self.dates_btn.set_solid_style()
        else:
            self.dates_btn.set_normal_style()
    