from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QFrame

from base_widgets import Btn, LayoutHor
from cfg import Dynamic, JsonData
from signals import SignalsApp
from styles import Names, Themes
from utils.main_utils import MainUtils

from .win_dates import WinDates

BTN_W, BTN_H = 80, 28


class DatesBtn(Btn):
    win_dates_opened = pyqtSignal()

    def __init__(self):
        super().__init__(text=Dynamic.lng.dates)
        self.setFixedSize(BTN_W, BTN_H)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        SignalsApp.all.btn_dates_style.connect(self.dates_btn_style)

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
    def __init__(self, text: str, true_name: str):
        super().__init__(text=text)
        self.setFixedSize(BTN_W, BTN_H)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.key = true_name

    def set_normal_style(self):
        self.setObjectName(Names.filter_btn)
        self.setStyleSheet(Themes.current)

    def set_blue_style(self):
        self.setObjectName(Names.filter_btn_selected)
        self.setStyleSheet(Themes.current)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        
        if self.objectName() == Names.filter_btn_selected:
            self.set_normal_style()
        else:
            self.set_blue_style()

        try:
            JsonData.cust_fltr_vals[self.key] = not JsonData.cust_fltr_vals[self.key]
        except KeyError:
            JsonData.sys_fltr_vals[self.key] = not JsonData.sys_fltr_vals[self.key]

        SignalsApp.all.grid_thumbnails_cmd.emit("reload")
        SignalsApp.all.grid_thumbnails_cmd.emit("to_top")

        return super().mouseReleaseEvent(ev)


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

        SignalsApp.all.bar_top_reset_filters.connect(self.disable_filters)

        self.init_ui()

    def init_ui(self):
        self.filter_btns.clear()

        for true_name, fake_name in Dynamic.lng.cust_fltr_names.items():
            label = FilterBtn(text=fake_name, true_name=true_name)
            self.h_layout.addWidget(label)

            if JsonData.cust_fltr_vals[true_name]:
                label.set_blue_style()
            else:
                label.set_normal_style()
            
            self.filter_btns.append(label)

        for true_name, fake_name in Dynamic.lng.sys_fltr_names.items():
            label = FilterBtn(text=fake_name, true_name=true_name)
            self.h_layout.addWidget(label)

            if JsonData.sys_fltr_vals[true_name]:
                label.set_blue_style()
            else:
                label.set_normal_style()

            self.filter_btns.append(label)

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
        self.win_dates.center_relative_parent(self)
        self.win_dates.show()

    def disable_filters(self):
        for i in self.filter_btns:
            i: FilterBtn
            i.set_normal_style()

        for i in JsonData.cust_fltr_vals:
            JsonData.cust_fltr_vals[i] = False

        for i in JsonData.sys_fltr_vals:
            JsonData.sys_fltr_vals[i] = False

    def reload_filters(self):
        MainUtils.clear_layout(self.h_layout)
        self.init_ui()
