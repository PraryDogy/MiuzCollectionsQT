from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QLabel, QWidget

from cfg import Dynamic, JsonData, Static
from system.filters import SystemFilter, UserFilter
from system.lang import Lang

from ._base_widgets import UHBoxLayout
from .wid_search import WidSearch

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
    reload_thumbnails = pyqtSignal()
    scroll_to_top = pyqtSignal()

    def __init__(self, filter: UserFilter):
        super().__init__(text=filter.lang_names[JsonData.lang_ind])

        self.filter = filter

        if self.filter.value:
            self.set_solid_style()
        else:
            self.set_normal_style()
        
    def toggle_cmd(self):
        self.filter.value = not self.filter.value

        if self.filter.value:
            self.set_solid_style()
        else:
            self.set_normal_style()

        self.reload_thumbnails.emit()
        self.scroll_to_top.emit()
    
    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        else:
            self.toggle_cmd()


class BarTop(QWidget):
    open_dates_win = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    scroll_to_top = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedHeight(35)
        self.h_layout = UHBoxLayout()
        self.setLayout(self.h_layout)
        self.filter_btns = []
        self.win_dates = None
        self.init_ui()

    def init_ui(self):
        self.filter_btns.clear()

        for filter in UserFilter.list_:
            label = FilterBtn(filter)
            label.reload_thumbnails.connect(lambda: self.reload_thumbnails.emit())
            label.scroll_to_top.connect(lambda: self.scroll_to_top.emit())
            self.filter_btns.append(label)
            self.h_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        label = FilterBtn(SystemFilter)
        label.reload_thumbnails.connect(lambda: self.reload_thumbnails.emit())
        label.scroll_to_top.connect(lambda: self.scroll_to_top.emit())
        self.filter_btns.append(label)
        self.h_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.dates_btn = DatesBtn()
        self.dates_btn.open_dates_win.connect(lambda: self.open_dates_win.emit())
        self.h_layout.addWidget(
            self.dates_btn,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        self.h_layout.addStretch(1)

        self.search_wid = WidSearch()
        self.search_wid.reload_thumbnails.connect(lambda: self.reload_thumbnails.emit())
        self.search_wid.scroll_to_top.connect(lambda: self.scroll_to_top.emit())
        self.h_layout.addWidget(
            self.search_wid,
            alignment=Qt.AlignmentFlag.AlignRight
        )

        if any((Dynamic.date_start, Dynamic.date_end)):
            self.dates_btn.set_solid_style()
        else:
            self.dates_btn.set_normal_style()
    