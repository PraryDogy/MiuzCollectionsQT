from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import QFrame, QSpacerItem, QWidget

from base_widgets import Btn, InputBase, LayoutH
from cfg import cnf
from signals import signals_app
from styles import Names, Themes
from utils.main_utils import MainUtils

from .win_dates import WinDates

BTN_W, BTN_H = 80, 28


class DatesBtn(Btn):
    win_dates_opened = pyqtSignal()

    def __init__(self):
        super().__init__(text=cnf.lng.dates)
        self.setFixedSize(BTN_W, BTN_H)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        signals_app.set_dates_btn_blue.connect(self.set_blue_style)
        signals_app.set_dates_btn_normal.connect(self.set_normal_style)
        signals_app.set_dates_btn_blue_border.connect(self.set_border_blue_style)

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
            cnf.cust_fltr_vals[self.key] = not cnf.cust_fltr_vals[self.key]
        except KeyError:
            cnf.sys_fltr_vals[self.key] = not cnf.sys_fltr_vals[self.key]

        signals_app.reload_thumbnails.emit()
        signals_app.scroll_top.emit()

        return super().mouseReleaseEvent(ev)


class SearchBarBase(InputBase):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(150)
        self.setFixedHeight(25)

        self.textChanged.connect(self.create_search)
        self.setPlaceholderText(cnf.lng.search)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.delayed_search)

        signals_app.clear_search.connect(self.clear_search)
        signals_app.set_focus_search.connect(self.setFocus)
        signals_app.reload_search_wid.connect(self.reload_search)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.clearFocus()
        return super().keyPressEvent(a0)

    def create_search(self, new_text):
        if len(new_text) > 0:
            cnf.search_widget_text = new_text
        else:
            cnf.search_widget_text = None

        self.timer.stop()
        self.timer.start()

    def delayed_search(self):
        signals_app.reload_thumbnails.emit()

    def clear_search(self):
        self.clear()
        cnf.search_widget_text = None

    def reload_search(self):
        self.setPlaceholderText(cnf.lng.search)


class WidSearch(QWidget):
    def __init__(self):
        super().__init__()

        h_layout = LayoutH()
        self.setLayout(h_layout)

        search = SearchBarBase()
        h_layout.addWidget(search)
        h_layout.addSpacerItem(QSpacerItem(5, 0))

        self.setFixedWidth(search.width() + 5)


class BarTop(QFrame):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(5, 0, 5, 0)
        self.setObjectName(Names.filter_bar_frame)
        self.setStyleSheet(Themes.current)
        self.setFixedHeight(34)

        self.h_layout = LayoutH(self)
        self.h_layout.setSpacing(0)
        self.h_layout.setContentsMargins(0, 0, 0, 0)

        self.filter_btns = []
        self.win_dates = None

        signals_app.disable_filters.connect(self.disable_filters)
        signals_app.reload_filters_bar.connect(self.reload_filters)

        self.init_ui()

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
        self.dates_btn.win_dates_opened.connect(self.open_win_dates)
        self.h_layout.addWidget(self.dates_btn)

        self.search_btn = WidSearch()
        self.h_layout.addWidget(self.search_btn, alignment=Qt.AlignmentFlag.AlignRight)

        if any((cnf.date_start, cnf.date_end)):
            self.dates_btn.set_blue_style()
        else:
            self.dates_btn.set_normal_style()

        self.setLayout(self.h_layout)
    
    def open_win_dates(self):
        self.win_dates = WinDates(parent=self)
        self.win_dates.show()

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
