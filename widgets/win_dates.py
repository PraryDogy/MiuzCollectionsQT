import calendar
import re
from datetime import datetime, timedelta
from typing import Literal

from PyQt5.QtCore import QDate, QLocale, Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QCalendarWidget, QLabel, QSpacerItem, QVBoxLayout,
                             QWidget)

from cfg import Dynamic, cfg
from system.lang import Lng

from ._base_widgets import (SingleActionWindow, SmallBtn, UHBoxLayout,
                            ULineEdit, UVBoxLayout)


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


# class DatesLineEdit(ULineEdit):
#     inputChangedSignal = pyqtSignal()

#     def __init__(self):
#         super().__init__()
#         self.setPlaceholderText(Lng.date_format[cfg.lng])
#         self.textChanged.connect(self.onTextChanged)
#         self.date = None

#     def convert_date(self, text: str):
#         try:
#             return DatesTools.text_to_datetime_date(text)
#         except (ValueError, TypeError):
#             return None

#     def re_date(self, text: str):
#         t_reg = re.match(r"\d{,2}\W\d{,2}\W\d{4}", text)
#         if t_reg:
#             return re.sub("\W", ".", t_reg.group(0))
#         else:
#             return None

#     def onTextChanged(self):
#         date_check = self.re_date(text=self.text())
#         new_date = self.convert_date(date_check)
#         pos = self.cursorPosition()

#         if new_date:
#             self.setText(date_check)
#             self.date = self.convert_date(date_check)
#         else:
#             self.date = None

#         self.setCursorPosition(pos)
#         self.inputChangedSignal.emit()

#     def keyPressEvent(self, a0):
#         pos = self.cursorPosition()
#         key = a0.key()

#         if not self.date:
#             self.date = datetime.today().date()

#         day, month, year = self.date.day, self.date.month, self.date.year
#         delta = 1 if key == Qt.Key_Up else -1

#         if key in (Qt.Key_Up, Qt.Key_Down):
#             # день
#             if pos in (0, 2):
#                 day += delta
#                 if day > calendar.monthrange(year, month)[1]:
#                     day = 1
#                     month += 1
#                     if month > 12:
#                         month = 1
#                         year += 1
#                 elif day < 1:
#                     month -= 1
#                     if month < 1:
#                         month = 12
#                         year -= 1
#                     day = calendar.monthrange(year, month)[1]

#             # месяц
#             elif pos in (3, 5):
#                 month += delta
#                 if month > 12:
#                     month = 1
#                     year += 1
#                 elif month < 1:
#                     month = 12
#                     year -= 1
#                 day = min(day, calendar.monthrange(year, month)[1])

#             # год
#             elif pos in range(6, 10):
#                 year += delta
#                 day = min(day, calendar.monthrange(year, month)[1])

#             self.date = datetime(year, month, day).date()
#             self.setText(DatesTools.date_to_text(self.date))
#             self.setCursorPosition(pos)
#             return

#         super().keyPressEvent(a0)






# class DatesTitle(QLabel):
#     def __init__(self, default_text: str):
#         self.default_text = default_text
#         super().__init__(self.default_text)

#     def set_named_date_text(self, date: datetime):
#         weekday = self.get_named_weekday(date)
#         named_date = self.get_named_date(date)
#         text = f"{named_date}, {weekday}"
#         self.setText(text)

#     def set_default_text(self):
#         self.setText(self.default_text)

#     def get_named_weekday(self, date: datetime) -> str:
#         day_number = str(date.weekday())
#         return Lng.weekdays_short[cfg.lng][day_number]
    
#     def get_named_date(self, date: datetime) -> str:
#         month_number = str(date.month)
#         month = Lng.months_genitive_case[cfg.lng][month_number]
#         return f"{date.day} {month} {date.year}"


# class DatesWid(QWidget):
#     dateChangedSignal = pyqtSignal()

#     def __init__(self, title_label_text: str):
#         super().__init__()

#         v_lay = UVBoxLayout()
#         v_lay.setSpacing(10)
#         self.setLayout(v_lay)

#         self.dates_title = DatesTitle(title_label_text)
#         v_lay.addWidget(self.dates_title)

#         self.input = MyCalendar()
#         # self.input.inputChangedSignal.connect(self.input_changed)
#         v_lay.addWidget(self.input)

#     def clear_input(self):
#         self.input.clear()

#     def input_changed(self):
#         date = self.get_datetime_date()

#         if date:
#             self.dates_title.set_named_date_text(date)
#         else:
#             self.dates_title.set_default_text()

#         self.dateChangedSignal.emit()

#     def get_datetime_date(self):
#         return self.input.date


# class LeftDateWidget(DatesWid):
#     def __init__(self):
#         text = Lng.start_date[cfg.lng]
#         super().__init__(text)

#         if Dynamic.date_start:
#             self.input.setText(DatesTools.date_to_text(Dynamic.date_start))


# class RightDateWidget(DatesWid):
#     def __init__(self):
#         text = Lng.end_date[cfg.lng]
#         super().__init__(text)

#         if Dynamic.date_end:
#             self.input.setText(DatesTools.date_to_text(Dynamic.date_end))


class MyCalendar(QWidget):
    dateSelected = pyqtSignal(QDate)

    def __init__(self, title: str):
        super().__init__()
        v_layout = UVBoxLayout(self)
        v_layout.setSpacing(10)

        title_label = QLabel(title)
        v_layout.addWidget(title_label)

        self.calendar = QCalendarWidget()
        self.calendar.setMaximumDate(QDate.currentDate())
        self.calendar.setMinimumDate(QDate(2000, 1, 1))
        self.calendar.setFixedSize(300, 300)
        v_layout.addWidget(self.calendar)
        if cfg.lng == 0:
            self.calendar.setLocale(QLocale(QLocale.Language.Russian))
        else:
            self.calendar.setLocale(QLocale(QLocale.Language.English))
        self.calendar.clicked.connect(self.on_date_clicked)

    def on_date_clicked(self, date: QDate):
        self.dateSelected.emit(date)

    def set_date(self, py_date):
        qdate = QDate(py_date.year, py_date.month, py_date.day)
        self.calendar.setSelectedDate(qdate)


class WinDates(SingleActionWindow):
    dates_btn_solid = pyqtSignal()
    dates_btn_normal = pyqtSignal()
    reload_thumbnails = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle(Lng.search_dates[cfg.lng])
        self.date_start = Dynamic.date_start
        self.date_end = Dynamic.date_end

        self.central_layout.setSpacing(10)
        self.central_layout.setContentsMargins(10, 10, 10, 10)

        dates_h_wid = QWidget()
        self.central_layout.addWidget(dates_h_wid)
        dates_h_lay = UHBoxLayout()
        dates_h_lay.setSpacing(10)
        dates_h_wid.setLayout(dates_h_lay)

        self.left_calendar = MyCalendar(Lng.start_date[cfg.lng])
        self.left_calendar.dateSelected.connect(
            lambda date: self.date_change(date=date, flag="start")
        )
        dates_h_lay.addWidget(self.left_calendar)
        if self.date_start:
            self.left_calendar.set_date(self.date_start)
        else:
            self.left_calendar.calendar.setSelectedDate(QDate()) 

        self.right_calendar = MyCalendar(Lng.end_date[cfg.lng])
        self.right_calendar.dateSelected.connect(
            lambda date: self.date_change(date=date, flag="end")
        )
        dates_h_lay.addWidget(self.right_calendar)
        if self.date_end:
            self.left_calendar.set_date(self.date_end)

        clear_btn = SmallBtn(text=Lng.reset[cfg.lng])
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

        self.ok_btn = SmallBtn(text=Lng.ok[cfg.lng])
        self.ok_btn.setFixedWidth(90)
        self.ok_btn.clicked.connect(self.ok_cmd)
        btns_h_lay.addWidget(self.ok_btn)

        spacer_item = QSpacerItem(10, 1)
        btns_h_lay.addItem(spacer_item)

        cancel_btn = SmallBtn(text=Lng.cancel[cfg.lng])
        self.ok_btn.setFixedWidth(90)
        cancel_btn.clicked.connect(self.cancel_cmd)
        btns_h_lay.addWidget(cancel_btn)
        btns_h_lay.addStretch(1)

        self.adjustSize()

    def clear_btn_cmd(self, *args):
        for i in (self.left_calendar, self.right_calendar):
            i.set_date(datetime.today().date())
        self.date_start = None
        self.date_end = None
        self.reload_thumbnails.emit()

    def date_change(self, date: QDate, flag: Literal["start", "end"]):
        date = date.toPyDate()
        if flag == "start":
            self.date_start = date
        else:
            self.date_end = date
    
    def named_date(self, date: datetime) -> str:
        return date.strftime("%d.%m.%Y")

    def ok_cmd(self, *args):
        # has_dates = True

        # if self.date_start and not self.date_end:
        #     self.date_end = datetime.today().date()
        
        # elif not self.date_start and not self.date_end:
        #     has_dates = False

        # elif not self.date_start and self.date_end:
        #     return

        if self.date_start and self.date_end:
            Dynamic.date_start = self.date_start
            Dynamic.date_end = self.date_end
            Dynamic.f_date_start = self.named_date(date=self.date_start)
            Dynamic.f_date_end = self.named_date(date=self.date_end)
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
        self.deleteLater()
        
    def mouseReleaseEvent(self, a0):
        self.setFocus()
        return super().mouseReleaseEvent(a0)
    
    def closeEvent(self, a0):
        if not all((Dynamic.date_start, Dynamic.date_end)):
            self.dates_btn_normal.emit()
        return super().closeEvent(a0)
    
    def deleteLater(self):
        if not all((Dynamic.date_start, Dynamic.date_end)):
            self.dates_btn_normal.emit()
        return super().deleteLater()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()

        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_cmd(a0)

        return super().keyPressEvent(a0)
