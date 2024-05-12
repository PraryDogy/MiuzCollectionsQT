from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame

from cfg import cnf
from signals import gui_signals_app
from utils import MainUtils

from base_widgets import Btn, LayoutH
from ..win_dates import WinDates
from styles import Styles, Names, default_theme


class Manager:
    win_dates: WinDates = None


class DatesBtn(Btn):
    def __init__(self):
        super().__init__(text=cnf.lng.dates)
        self.setFixedSize(Styles.topbar_item_w, Styles.topbar_item_h)
        self.setAlignment(Qt.AlignCenter)

        gui_signals_app.set_dates_btn_blue.connect(self.set_blue_style)
        gui_signals_app.set_dates_btn_normal.connect(self.set_normal_style)
        gui_signals_app.set_dates_btn_blue_border.connect(self.set_border_blue_style)

    def set_normal_style(self):
        self.setObjectName(Names.dates_btn)
        self.setStyleSheet(default_theme)

    def set_blue_style(self):
        self.setObjectName(Names.dates_btn_selected)
        self.setStyleSheet(default_theme)

    def set_border_blue_style(self):
        self.setObjectName(Names.dates_btn_bordered)
        self.setStyleSheet(default_theme)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            Manager.win_dates = WinDates()
            Manager.win_dates.show()


class FilterBtn(Btn):
    def __init__(self, text: str, true_name: str):
        super().__init__(text=text)
        self.setFixedSize(Styles.topbar_item_w, Styles.topbar_item_h)
        self.setAlignment(Qt.AlignCenter)

        self.key = true_name

    def set_normal_style(self):
        self.setObjectName(Names.filter_btn)
        self.setStyleSheet(default_theme)

    def set_blue_style(self):
        self.setObjectName(Names.filter_btn_selected)
        self.setStyleSheet(default_theme)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        
        if self.objectName() == Names.filter_btn_selected:
            self.set_normal_style()
        else:
            self.set_blue_style()

        try:
            cnf.cust_fltr_vals[self.key] = not cnf.cust_fltr_vals[self.key]
        except KeyError:
            cnf.sys_fltr_vals[self.key] = not cnf.sys_fltr_vals[self.key]

        gui_signals_app.reload_thumbnails.emit()
        gui_signals_app.scroll_top.emit()


class FiltersBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(*Styles.topbar_marg)
        self.setObjectName(Names.filter_bar_frame)
        self.setStyleSheet(default_theme)
        self.setFixedHeight(34)

        self.h_layout = LayoutH(self)
        self.h_layout.setSpacing(0)
        self.h_layout.setContentsMargins(0, 0, 0, 0)

        self.filter_btns = []
        self.init_ui()

        gui_signals_app.disable_filters.connect(self.disable_filters)
        gui_signals_app.reload_filters_bar.connect(self.reload_filters)

    def init_ui(self):
        self.filter_btns.clear()

        for true_name, fake_name in cnf.lng.cust_fltr_names.items():
            label = FilterBtn(text=fake_name, true_name=true_name)
            self.h_layout.addWidget(label)

            if cnf.cust_fltr_vals[true_name]:
                label.set_blue_style()
            else:
                label.set_normal_style()
            
            self.filter_btns.append(label)

        for true_name, fake_name in cnf.lng.sys_fltr_names.items():
            label = FilterBtn(text=fake_name, true_name=true_name)
            self.h_layout.addWidget(label)

            if cnf.sys_fltr_vals[true_name]:
                label.set_blue_style()
            else:
                label.set_normal_style()

            self.filter_btns.append(label)

        self.dates_btn = DatesBtn()
        self.h_layout.addWidget(self.dates_btn)

        if any((cnf.date_start, cnf.date_end)):
            self.dates_btn.set_blue_style()
        else:
            self.dates_btn.set_normal_style()

        self.h_layout.addStretch(1)
        self.setLayout(self.h_layout)

    def disable_filters(self):
        for i in self.filter_btns:
            i: FilterBtn
            i.set_normal_style()

        for i in cnf.cust_fltr_vals:
            cnf.cust_fltr_vals[i] = False

        for i in cnf.sys_fltr_vals:
            cnf.sys_fltr_vals[i] = False

    def reload_filters(self):
        MainUtils.clear_layout(self.h_layout)
        self.init_ui()
