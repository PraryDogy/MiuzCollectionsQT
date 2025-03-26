import re
from datetime import datetime, timedelta
from functools import partial
from typing import Literal

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLabel, QPushButton, QSpacerItem, QWidget

from base_widgets import LayoutHor, LayoutVer
from base_widgets.input import ULineEdit
from base_widgets.wins import WinSystem
from cfg import Dynamic
from lang import Lang
from signals import SignalsApp


class DatesTools:

    @classmethod
    def solid_or_normal_style(cls):
        if not Dynamic.date_start:
            SignalsApp.instance.btn_dates_style.emit("normal")
        else:
            SignalsApp.instance.btn_dates_style.emit("solid")

    @classmethod
    def border_style(cls):
        SignalsApp.instance.btn_dates_style.emit("border")

    @classmethod
    def date_to_text(cls, date: datetime):
        return date.strftime("%d.%m.%Y")

    @classmethod
    def add_or_subtract_days(cls, date: datetime, days: int):
        return date + timedelta(days=days)
    
    @classmethod
    def text_to_datetime_date(cls, text: str):
        return datetime.strptime(text, "%d.%m.%Y").date()


class DatesLineEdit(ULineEdit):
    inputChangedSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(150)
        self.setPlaceholderText(Lang.d_m_y)
        self.textChanged.connect(self.onTextChanged)
        self.date = None

    def convert_date(self, text: str):
        try:
            return DatesTools.text_to_datetime_date(text)
        except (ValueError, TypeError):
            return None

    def re_date(self, text: str):
        t_reg = re.match(r"\d{,2}\W\d{,2}\W\d{4}", text)
        if t_reg:
            return re.sub("\W", ".", t_reg.group(0))
        else:
            return None

    def onTextChanged(self):
        date_check = self.re_date(text=self.text())
        new_date = self.convert_date(date_check)

        if new_date:
            self.setText(date_check)
            self.date = self.convert_date(date_check)
        else:
            self.date = None

        self.inputChangedSignal.emit()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Up:
            if self.date:
                self.date = DatesTools.add_or_subtract_days(self.date, 1)
                self.setText(DatesTools.date_to_text(self.date))
            else:
                self.date = datetime.today().date()
                self.setText(DatesTools.date_to_text(self.date))

        elif a0.key() == Qt.Key.Key_Down:
            if self.date:
                self.date = DatesTools.add_or_subtract_days(self.date, -1)
                self.setText(DatesTools.date_to_text(self.date))
            else:
                self.date = datetime.today().date()
                self.setText(DatesTools.date_to_text(self.date))

        return super().keyPressEvent(a0)


class DatesTitle(QLabel):
    def __init__(self, default_text: str):
        self.default_text = "\n" + default_text

        super().__init__(self.default_text)
        self.setFixedWidth(150)

    def set_named_date_text(self, date: datetime):
        weekday = self.get_named_weekday(date).capitalize()
        named_date = self.get_named_date(date)

        self.setText(f"{weekday}:\n{named_date}")

    def set_default_text(self):
        self.setText(self.default_text)

    def get_named_weekday(self, date: datetime) -> str:
        day_number = str(date.weekday())
        return Lang.weekdays[day_number]
    
    def get_named_date(self, date: datetime) -> str:
        month_number = str(date.month)
        month = Lang.months_genitive_case[month_number]
        return f"{date.day} {month} {date.year}"


class DatesWid(QWidget):
    dateChangedSignal = pyqtSignal()

    def __init__(self, title_label_text):
        super().__init__()

        v_lay = LayoutVer()
        v_lay.setSpacing(5)
        self.setLayout(v_lay)

        self.dates_title = DatesTitle(title_label_text)
        v_lay.addWidget(self.dates_title)

        self.input = DatesLineEdit()
        self.input.inputChangedSignal.connect(self.input_changed)
        v_lay.addWidget(self.input)

    def clear_input(self):
        self.input.clear()

    def input_changed(self):
        date = self.get_datetime_date()

        if date:
            self.dates_title.set_named_date_text(date)
        else:
            self.dates_title.set_default_text()

        self.dateChangedSignal.emit()

    def get_datetime_date(self):
        return self.input.date


class LeftDateWidget(DatesWid):
    def __init__(self):
        super().__init__(Lang.start)

        if Dynamic.date_start:
            self.input.setText(DatesTools.date_to_text(Dynamic.date_start))


class RightDateWidget(DatesWid):
    def __init__(self):
        super().__init__(Lang.end)

        if Dynamic.date_end:
            self.input.setText(DatesTools.date_to_text(Dynamic.date_end))


class WinDates(WinSystem):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(Lang.dates)
        DatesTools.border_style()
        self.date_start = Dynamic.date_start
        self.date_end = Dynamic.date_end

        main_title = QLabel(Lang.search_dates)
        self.central_layout.addWidget(main_title)

        dates_h_wid = QWidget()
        self.central_layout.addWidget(dates_h_wid)
        dates_h_lay = LayoutHor()
        dates_h_wid.setLayout(dates_h_lay)

        left_cmd = lambda: self.date_change(flag="start")
        self.left_date_wid = LeftDateWidget()
        self.left_date_wid.dateChangedSignal.connect(left_cmd)
        dates_h_lay.addWidget(self.left_date_wid)

        spacer_item = QSpacerItem(10, 1)
        dates_h_lay.addItem(spacer_item)

        right_cmd = lambda: self.date_change(flag="end")
        self.right_date_wid = RightDateWidget()
        self.right_date_wid.dateChangedSignal.connect(right_cmd)
        dates_h_lay.addWidget(self.right_date_wid)

        spacer_item = QSpacerItem(1, 5)
        self.central_layout.addItem(spacer_item)

        clear_btn = QPushButton(text=Lang.reset)
        clear_btn.setFixedWidth(100)
        clear_btn.clicked.connect(self.clear_btn_cmd)
        self.central_layout.addWidget(
            clear_btn,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        spacer_item = QSpacerItem(1, 10)
        self.central_layout.addItem(spacer_item)

        # ok cancel button # ok cancel button # ok cancel button # ok cancel button

        btns_h_wid = QWidget()
        self.central_layout.addWidget(btns_h_wid)
        btns_h_lay = LayoutHor()
        btns_h_wid.setLayout(btns_h_lay)

        btns_h_lay.addStretch(1)
        btns_h_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ok_btn = QPushButton(text=Lang.ok)
        self.ok_btn.setFixedWidth(90)
        self.ok_btn.clicked.connect(self.ok_cmd)
        btns_h_lay.addWidget(self.ok_btn)

        spacer_item = QSpacerItem(10, 1)
        btns_h_lay.addItem(spacer_item)

        cancel_btn = QPushButton(text=Lang.cancel)
        self.ok_btn.setFixedWidth(90)
        cancel_btn.clicked.connect(self.cancel_cmd)
        btns_h_lay.addWidget(cancel_btn)
        btns_h_lay.addStretch(1)

        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

    @classmethod
    def reset_dates(cls, *args):
        Dynamic.date_start, Dynamic.date_end = None, None
        Dynamic.f_date_start, Dynamic.f_date_end = None, None

        Dynamic.grid_offset = 0

        SignalsApp.instance.btn_dates_style.emit("normal")
        SignalsApp.instance.grid_thumbnails_cmd.emit("reload")
        SignalsApp.instance.grid_thumbnails_cmd.emit("to_top")

    def clear_btn_cmd(self, *args):
        for i in (self.left_date_wid, self.right_date_wid):
            i.clear_input()

    def date_change(self, flag: Literal["start", "end"]):
        if flag == "start":
            new_date = self.left_date_wid.get_datetime_date()
            self.date_start = new_date
        else:
            new_date = self.right_date_wid.get_datetime_date()
            self.date_end = new_date

    def named_date(self, date: datetime):
        month = Lang.months_genitive_case[str(date.month)]
        return f"{date.day} {month} {date.year}"

    def ok_cmd(self, *args):
        if self.date_start and not self.date_end:
            self.date_end = datetime.today().date()
            has_dates = True

        elif self.date_start and self.date_end:
            has_dates = True
        
        elif not self.date_start and not self.date_end:
            has_dates = False

        elif not self.date_start and self.date_end:
            return

        if has_dates:
            Dynamic.date_start = self.date_start
            Dynamic.date_end = self.date_end

            Dynamic.f_date_start = self.named_date(date=Dynamic.date_start)
            Dynamic.f_date_end = self.named_date(date=Dynamic.date_end)

        else:
            self.reset_dates()

        DatesTools.solid_or_normal_style()
        self.close()

        SignalsApp.instance.grid_thumbnails_cmd.emit("reload")

    def cancel_cmd(self, *args):
        DatesTools.solid_or_normal_style()
        self.close()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            DatesTools.solid_or_normal_style()
            self.close()

        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd(a0)

        return super().keyPressEvent(a0)
