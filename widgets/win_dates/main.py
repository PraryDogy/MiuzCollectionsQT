from datetime import datetime
from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QSpacerItem

from base_widgets import (Btn, WinStandartBase, LayoutH,
                          LayoutV)
from cfg import cnf
from signals import gui_signals_app
from utils import MainUtils

from .date_utils import DateUtils
from .input_wid import BaseDateInput
from .label_title import TitleLabel


class FiltersDateBtncolor:

    @staticmethod
    def date_based_color():
        if not cnf.date_start:
            gui_signals_app.set_dates_btn_normal.emit()
        else:
            gui_signals_app.set_dates_btn_blue.emit()

    @staticmethod
    def set_border():
        gui_signals_app.set_dates_btn_blue_border.emit()


class BaseDateLayout(LayoutV):
    dateChangedSignal = pyqtSignal()

    def __init__(self, title_label_text):
        super().__init__()

        self.title_label = TitleLabel(title_label_text)
        self.addWidget(self.title_label)

        spacer_item = QSpacerItem(1, 5)
        self.addItem(spacer_item)

        self.input = BaseDateInput()
        self.input.inputChangedSignal.connect(self.input_changed)
        self.addWidget(self.input)

    def input_changed(self):
        date = self.get_datetime_date()

        if date:
            self.title_label.set_named_date_text(date)
        else:
            self.title_label.set_default_text()

        self.dateChangedSignal.emit()

    def get_datetime_date(self):
        return self.input.date


class LeftDateLayout(BaseDateLayout):
    def __init__(self):
        super().__init__(cnf.lng.start)

        if cnf.date_start:
            self.input.setText(DateUtils.date_to_text(cnf.date_start))


class RightDateLayout(BaseDateLayout):
    def __init__(self):
        super().__init__(cnf.lng.end)

        if cnf.date_end:
            self.input.setText(DateUtils.date_to_text(cnf.date_end))


class DatesWinBase(WinStandartBase):
    def __init__(self):
        MainUtils.close_same_win(WinDates)

        super().__init__(close_func=self.my_close)

        FiltersDateBtncolor.set_border()
        self.date_start = cnf.date_start
        self.date_end = cnf.date_end
        self.disable_min_max()

    def my_close(self, event):
        self.delete_win.emit()
        FiltersDateBtncolor.date_based_color()
        self.deleteLater()
        gui_signals_app.set_focus_viewer.emit()
        event.ignore()


class WinDates(DatesWinBase):
    def __init__(self):
        super().__init__()
        self.set_title(cnf.lng.dates)

        self.init_ui()
        self.fit_size()
        self.center_win()

    def init_ui(self):
        title_label = QLabel(cnf.lng.search_dates)
        title_label.setContentsMargins(0, 0, 0, 5)
        self.content_layout.addWidget(title_label)

        widget_layout = LayoutH()
        self.content_layout.addLayout(widget_layout)

        self.left_date = LeftDateLayout()
        self.left_date.dateChangedSignal.connect(partial(self.date_change, "start"))
        widget_layout.addLayout(self.left_date)

        spacer_item = QSpacerItem(10, 1)
        widget_layout.addItem(spacer_item)

        self.right_date = RightDateLayout()
        self.right_date.dateChangedSignal.connect(partial(self.date_change, "end"))
        widget_layout.addLayout(self.right_date)

        # ok cancel button

        buttons_layout = LayoutH()
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        self.content_layout.addLayout(buttons_layout)

        buttons_layout.addStretch(1)
        buttons_layout.setAlignment(Qt.AlignCenter)
        self.ok_label = Btn(cnf.lng.ok)
        self.ok_label.mouseReleaseEvent = self.ok_cmd
        buttons_layout.addWidget(self.ok_label)

        spacer_item = QSpacerItem(10, 1)
        buttons_layout.addItem(spacer_item)

        cancel_label = Btn(cnf.lng.cancel)
        cancel_label.mouseReleaseEvent = self.cancel_cmd
        buttons_layout.addWidget(cancel_label)
        buttons_layout.addStretch(1)

    def date_change(self, flag: str):
        if flag == "start":
            new_date = self.left_date.get_datetime_date()
            self.date_start = new_date
        else:
            new_date = self.right_date.get_datetime_date()
            self.date_end = new_date

        if new_date:
            self.ok_label.setDisabled(False)
        else:
            self.ok_label.setDisabled(True)

    def named_date(self, date: datetime):
        month = cnf.lng.months_genitive_case[str(date.month)]
        return f"{date.day} {month} {date.year}"

    def ok_cmd(self, event):
        if not any((self.date_start, self.date_end)):
            cnf.date_start, cnf.date_end = None, None
            FiltersDateBtncolor.date_based_color()
            self.deleteLater()

            gui_signals_app.set_focus_viewer.emit()
            gui_signals_app.reload_thumbnails.emit()

            return

        elif not self.date_start:
            self.date_start = self.date_end

        elif not self.date_end:
            self.date_end = self.date_start

        cnf.date_start = self.date_start
        cnf.date_end = self.date_end

        cnf.date_start_text = self.named_date(date=cnf.date_start)
        cnf.date_end_text = self.named_date(date=cnf.date_end)

        FiltersDateBtncolor.date_based_color()
        self.delete_win.emit()
        self.deleteLater()

        gui_signals_app.reload_thumbnails.emit()
        gui_signals_app.set_focus_viewer.emit()

    def cancel_cmd(self, event):
        FiltersDateBtncolor.date_based_color()
        self.delete_win.emit()
        self.deleteLater()

        gui_signals_app.set_focus_viewer.emit()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            FiltersDateBtncolor.date_based_color()
            self.delete_win.emit()
            self.deleteLater()
            gui_signals_app.set_focus_viewer.emit()

        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.ok_cmd(event)

        super().keyPressEvent(event)
