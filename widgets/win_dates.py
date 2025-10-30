import calendar
import re
from datetime import datetime, timedelta
from typing import Literal

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLabel, QPushButton, QSpacerItem, QWidget

from cfg import Dynamic, cfg
from system.lang import Lng

from ._base_widgets import (SingleActionWindow, UHBoxLayout, ULineEdit,
                            UVBoxLayout)


class DatesTools:
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
        self.setPlaceholderText(Lng.date_format[cfg.lng])
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


    def keyPressEvent(self, a0):
        pos = self.cursorPosition()
        key = a0.key()

        if not self.date:
            self.date = datetime.today().date()

        day, month, year = self.date.day, self.date.month, self.date.year
        delta = 1 if key == Qt.Key_Up else -1

        if key in (Qt.Key_Up, Qt.Key_Down):
            # день
            if pos in (0, 1):
                day += delta
                if day > calendar.monthrange(year, month)[1]:
                    day = 1
                    month += 1
                    if month > 12:
                        month = 1
                        year += 1
                elif day < 1:
                    month -= 1
                    if month < 1:
                        month = 12
                        year -= 1
                    day = calendar.monthrange(year, month)[1]

            # месяц
            elif pos in (3, 4):
                month += delta
                if month > 12:
                    month = 1
                    year += 1
                elif month < 1:
                    month = 12
                    year -= 1
                day = min(day, calendar.monthrange(year, month)[1])

            # год
            elif pos in range(6, 10):
                year += delta
                day = min(day, calendar.monthrange(year, month)[1])

            self.date = datetime(year, month, day).date()
            self.setText(DatesTools.date_to_text(self.date))
            self.setCursorPosition(pos)
            return

        super().keyPressEvent(a0)


class DatesTitle(QLabel):
    def __init__(self, default_text: str):
        self.default_text = default_text

        super().__init__(self.default_text)

    def set_named_date_text(self, date: datetime):
        weekday = self.get_named_weekday(date)
        named_date = self.get_named_date(date)
        text = f"{named_date}, {weekday}"
        self.setText(text)

    def set_default_text(self):
        self.setText(self.default_text)

    def get_named_weekday(self, date: datetime) -> str:
        day_number = str(date.weekday())
        return Lng.weekdays_short[cfg.lng][day_number]
    
    def get_named_date(self, date: datetime) -> str:
        month_number = str(date.month)
        month = Lng.months_genitive_case[cfg.lng][month_number]
        return f"{date.day} {month} {date.year}"


class DatesWid(QWidget):
    dateChangedSignal = pyqtSignal()

    def __init__(self, title_label_text: str):
        super().__init__()

        v_lay = UVBoxLayout()
        v_lay.setSpacing(10)
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
        text = Lng.start_date[cfg.lng]
        super().__init__(text)

        if Dynamic.date_start:
            self.input.setText(DatesTools.date_to_text(Dynamic.date_start))


class RightDateWidget(DatesWid):
    def __init__(self):
        text = Lng.end_date[cfg.lng]
        super().__init__(text)

        if Dynamic.date_end:
            self.input.setText(DatesTools.date_to_text(Dynamic.date_end))


class WinDates(SingleActionWindow):
    date_wid_width = 150
    dates_btn_solid = pyqtSignal()
    dates_btn_normal = pyqtSignal()
    reload_thumbnails = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle(Lng.dates[cfg.lng])
        self.date_start = Dynamic.date_start
        self.date_end = Dynamic.date_end

        self.central_layout.setSpacing(10)
        self.central_layout.setContentsMargins(10, 10, 10, 10)

        main_title = QLabel(Lng.search_dates[cfg.lng])
        self.central_layout.addWidget(main_title)

        dates_h_wid = QWidget()
        self.central_layout.addWidget(dates_h_wid)
        dates_h_lay = UHBoxLayout()
        dates_h_lay.setSpacing(10)
        dates_h_wid.setLayout(dates_h_lay)

        left_cmd = lambda: self.date_change(flag="start")
        self.left_date_wid = LeftDateWidget()
        self.left_date_wid.setFixedWidth(self.date_wid_width)
        self.left_date_wid.dateChangedSignal.connect(left_cmd)
        dates_h_lay.addWidget(self.left_date_wid)

        right_cmd = lambda: self.date_change(flag="end")
        self.right_date_wid = RightDateWidget()
        self.right_date_wid.setFixedWidth(self.date_wid_width)
        self.right_date_wid.dateChangedSignal.connect(right_cmd)
        dates_h_lay.addWidget(self.right_date_wid)

        clear_btn = QPushButton(text=Lng.reset[cfg.lng])
        clear_btn.setFixedWidth(100)
        clear_btn.clicked.connect(self.clear_btn_cmd)
        self.central_layout.addWidget(
            clear_btn,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        # ok cancel button # ok cancel button # ok cancel button # ok cancel button

        btns_h_wid = QWidget()
        self.central_layout.addWidget(btns_h_wid)
        btns_h_lay = UHBoxLayout()
        btns_h_wid.setLayout(btns_h_lay)

        btns_h_lay.addStretch(1)
        btns_h_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ok_btn = QPushButton(text=Lng.ok[cfg.lng])
        self.ok_btn.setFixedWidth(90)
        self.ok_btn.clicked.connect(self.ok_cmd)
        btns_h_lay.addWidget(self.ok_btn)

        spacer_item = QSpacerItem(10, 1)
        btns_h_lay.addItem(spacer_item)

        cancel_btn = QPushButton(text=Lng.cancel[cfg.lng])
        self.ok_btn.setFixedWidth(90)
        cancel_btn.clicked.connect(self.cancel_cmd)
        btns_h_lay.addWidget(cancel_btn)
        btns_h_lay.addStretch(1)

        self.adjustSize()

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

    # def named_date(self, date: datetime):
    #     month = Lng.months_genitive_case[Cfg.lng][str(date.month)]
    #     return f"{date.day} {month} {date.year}"
    
    def named_date(self, date: datetime) -> str:
        return date.strftime("%d.%m.%Y")

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
            self.reload_thumbnails.emit()
            self.dates_btn_solid.emit()
        else:
            Dynamic.date_start, Dynamic.date_end = None, None
            Dynamic.f_date_start, Dynamic.f_date_end = None, None
            Dynamic.loaded_thumbs = 0
            self.reload_thumbnails.emit()
            self.dates_btn_normal.emit()

        self.deleteLater()

    def cancel_cmd(self, *args):
        self.dates_btn_normal.emit()
        self.deleteLater()
        
    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.dates_btn_normal.emit()
            self.deleteLater()

        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd(a0)

        return super().keyPressEvent(a0)
