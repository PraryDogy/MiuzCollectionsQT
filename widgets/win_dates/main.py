from datetime import datetime
from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLabel, QSpacerItem, QWidget

from base_widgets import Btn, LayoutH, LayoutV, WinStandartBase
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


class BaseDateLayout(QWidget):
    dateChangedSignal = pyqtSignal()

    def __init__(self, title_label_text):
        super().__init__()

        layout_v = LayoutV()
        self.setLayout(layout_v)

        self.title_label = TitleLabel(title_label_text)
        layout_v.addWidget(self.title_label)

        spacer_item = QSpacerItem(1, 5)
        layout_v.addSpacerItem(spacer_item)

        self.input = BaseDateInput()
        self.input.inputChangedSignal.connect(self.input_changed)
        layout_v.addWidget(self.input)

    def input_changed(self):
        date = self.get_datetime_date()

        if date:
            self.title_label.set_named_date_text(date)
        else:
            self.title_label.set_default_text()

        self.dateChangedSignal.emit()

    def get_datetime_date(self):
        return self.input.date


class LeftDateWidget(BaseDateLayout):
    def __init__(self):
        super().__init__(cnf.lng.start)

        if cnf.date_start:
            self.input.setText(DateUtils.date_to_text(cnf.date_start))


class RightDateWidget(BaseDateLayout):
    def __init__(self):
        super().__init__(cnf.lng.end)

        if cnf.date_end:
            self.input.setText(DateUtils.date_to_text(cnf.date_end))


class WinDates(WinStandartBase):
    def __init__(self, parent: QWidget):
        super().__init__(close_func=self.my_close)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        FiltersDateBtncolor.set_border()
        self.disable_min()
        self.disable_max()
        self.set_title(cnf.lng.dates)

        self.date_start = cnf.date_start
        self.date_end = cnf.date_end

        self.init_ui()
        self.fit_size()
        self.center_win(parent=parent)

    def init_ui(self):
        title_label = QLabel(cnf.lng.search_dates)
        title_label.setContentsMargins(0, 0, 0, 5)
        self.content_layout.addWidget(title_label)

        widget_wid = QWidget()
        widget_layout = LayoutH()
        widget_wid.setLayout(widget_layout)
        self.content_layout.addWidget(widget_wid)

        self.left_date = LeftDateWidget()
        self.left_date.dateChangedSignal.connect(partial(self.date_change, "start"))
        widget_layout.addWidget(self.left_date)

        spacer_item = QSpacerItem(10, 1)
        widget_layout.addItem(spacer_item)

        self.right_date = RightDateWidget()
        self.right_date.dateChangedSignal.connect(partial(self.date_change, "end"))
        widget_layout.addWidget(self.right_date)

        # ok cancel button

        buttons_wid = QWidget()
        buttons_layout = LayoutH()
        buttons_wid.setLayout(buttons_layout)
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        self.content_layout.addWidget(buttons_wid)

        buttons_layout.addStretch(1)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
            return
            # cnf.date_start, cnf.date_end = None, None
            # FiltersDateBtncolor.date_based_color()
            # self.close()
            # gui_signals_app.reload_thumbnails.emit()

            return

        elif not self.date_start:
            return
            # self.date_start = self.date_end

        elif not self.date_end:
            self.date_end = self.date_start
            self.date_end = datetime.today().date()
            print(self.date_end)

        cnf.date_start = self.date_start
        cnf.date_end = self.date_end

        cnf.date_start_text = self.named_date(date=cnf.date_start)
        cnf.date_end_text = self.named_date(date=cnf.date_end)

        FiltersDateBtncolor.date_based_color()
        self.close()

        gui_signals_app.reload_thumbnails.emit()

    def cancel_cmd(self, event):
        FiltersDateBtncolor.date_based_color()
        self.close()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            FiltersDateBtncolor.date_based_color()
            self.close()

        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd(a0)
        return super().keyPressEvent(a0)

    def my_close(self, event):
        FiltersDateBtncolor.date_based_color()
        self.close()