from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent, QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import QAction, QFrame, QLabel, QWidget

from base_widgets import Btn, ContextCustom, InputBase, LayoutHor
from base_widgets.wins import WinChild
from cfg import Dynamic, Filter, JsonData
from lang import Lang
from signals import SignalsApp
from styles import Names, Themes

from .win_dates import WinDates

BTN_W, BTN_H = 80, 28



class DatesBtn(Btn):
    win_dates_opened = pyqtSignal()

    def __init__(self):
        super().__init__(text=Lang.dates)
        self.setFixedSize(BTN_W, BTN_H)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        SignalsApp.all_.btn_dates_style.connect(self.dates_btn_style)

    def dates_btn_style(self, flag: str):
        if flag == "blue":
            self.set_blue_style()
        elif flag == "normal":
            self.set_normal_style()
        elif flag == "border":
            self.set_border_blue_style()
        else:
            raise Exception("widgets > bar_top > dates btn > wrong flag", flag)

    def set_normal_style(self):
        self.setObjectName(Names.dates_btn)
        self.setStyleSheet(Themes.current)

    def set_blue_style(self):
        self.setObjectName(Names.dates_btn_selected)
        self.setStyleSheet(Themes.current)

    def set_border_blue_style(self):
        self.setObjectName(Names.dates_btn_bordered)
        self.setStyleSheet(Themes.current)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.win_dates_opened.emit()
        return super().mouseReleaseEvent(ev)


class FilterBtn(Btn):
    def __init__(self, filter: Filter):
        super().__init__(text=filter.names[JsonData.lang_ind])

        self.filter = filter
        self.setFixedSize(BTN_W, BTN_H)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if filter.value:
            self.set_blue_style()
        else:
            self.set_normal_style()

    def set_normal_style(self):
        self.setObjectName(Names.filter_btn)
        self.setStyleSheet(Themes.current)

    def set_blue_style(self):
        self.setObjectName(Names.filter_btn_selected)
        self.setStyleSheet(Themes.current)

    def set_border_blue_style(self):
        self.setObjectName(Names.dates_btn_bordered)
        self.setStyleSheet(Themes.current)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        
        self.filter.value = not self.filter.value

        if self.filter.value:
            self.set_blue_style()
        else:
            self.set_normal_style()

        SignalsApp.all_.grid_thumbnails_cmd.emit("reload")
        SignalsApp.all_.grid_thumbnails_cmd.emit("to_top")
    
    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        prev_name = self.objectName()
        self.set_border_blue_style()
        menu_ = ContextCustom(ev)

        t = "Выбрать/отключить"
        menu_.addAction(QAction(parent=menu_, text=t))

        menu_.show_menu()

        if prev_name == Names.filter_btn:
            self.set_normal_style()
        else:
            self.set_blue_style()


class BarTop(QFrame):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(5, 0, 5, 0)
        self.setObjectName(Names.filter_bar_frame)
        self.setStyleSheet(Themes.current)
        self.setFixedHeight(34)

        self.h_layout = LayoutHor(self)
        self.h_layout.setSpacing(0)
        self.h_layout.setContentsMargins(0, 0, 0, 0)

        self.filter_btns = []
        self.win_dates = None

        SignalsApp.all_.bar_top_reset_filters.connect(self.disable_filters)

        self.init_ui()

    def init_ui(self):
        self.filter_btns.clear()

        for filter in Filter.filters:
            label = FilterBtn(filter)
            self.filter_btns.append(label)
            self.h_layout.addWidget(label)
        
        self.dates_btn = DatesBtn()
        self.dates_btn.win_dates_opened.connect(self.open_win_dates)
        self.h_layout.addWidget(self.dates_btn)

        if any((Dynamic.date_start, Dynamic.date_end)):
            self.dates_btn.set_blue_style()
        else:
            self.dates_btn.set_normal_style()

        self.h_layout.addStretch(1)
        self.setLayout(self.h_layout)
    
    def open_win_dates(self):
        self.win_dates = WinDates()
        self.win_dates.center_relative_parent(self.window())
        self.win_dates.show()

    def disable_filters(self):
        for i in self.filter_btns:
            i: FilterBtn
            i.set_normal_style()

        for filter in Filter.filters:
            filter.value = False