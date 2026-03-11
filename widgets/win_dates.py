import calendar
import re
from datetime import datetime, timedelta
from typing import Literal

from PyQt5.QtCore import QDate, QLocale, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QCalendarWidget, QFrame, QLabel, QSpacerItem,
                             QVBoxLayout, QWidget)

from cfg import Dynamic, cfg
from system.lang import Lng

from ._base_widgets import (HSep, SingleActionWindow, SmallBtn, UHBoxLayout,
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


class MyCalendar(QFrame):
    dateSelected = pyqtSignal(QDate)

    def __init__(self, title: str):
        super().__init__()
        v_layout = UVBoxLayout(self)
        v_layout.setSpacing(10)

        self.title = DatesTitle(title)
        v_layout.addWidget(self.title)

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

    def set_date(self, py_date: datetime):
        qdate = QDate(py_date.year, py_date.month, py_date.day)
        print(qdate, qdate.isValid())  # проверка
        QTimer.singleShot(100, lambda: self.calendar.setSelectedDate(qdate))
        # self.calendar.setCurrentPage(qdate.year(), qdate.month())


class WinDates(SingleActionWindow):
    dates_btn_solid = pyqtSignal()
    dates_btn_normal = pyqtSignal()
    reload_thumbnails = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lng.search_dates[cfg.lng])

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

        self.right_calendar = MyCalendar(Lng.end_date[cfg.lng])
        self.right_calendar.dateSelected.connect(
            lambda date: self.date_change(date=date, flag="end")
        )
        dates_h_lay.addWidget(self.right_calendar)

        self.central_layout.addWidget(HSep())

        clear_btn = SmallBtn(text=Lng.reset[cfg.lng])
        clear_btn.setFixedWidth(100)
        clear_btn.clicked.connect(self.clear_btn_cmd)
        self.central_layout.addWidget(
            clear_btn,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.adjustSize()

        if Dynamic.date_start:
            self.left_calendar.set_date(Dynamic.date_start)
            self.left_calendar.title.set_named_date_text(Dynamic.date_start)
        if Dynamic.date_end:
            self.right_calendar.set_date(Dynamic.date_end)
            self.right_calendar.title.set_named_date_text(Dynamic.date_end)

    def clear_btn_cmd(self, *args):
        Dynamic.loaded_thumbs = 0
        Dynamic.date_start = None
        Dynamic.date_end = None
        Dynamic.f_date_start = None
        Dynamic.f_date_end = None
        self.reload_thumbnails.emit()
        self.dates_btn_normal.emit()
        self.deleteLater()

    def date_change(self, date: QDate, flag: Literal["start", "end"]):
        date = date.toPyDate()
        if flag == "start":
            Dynamic.date_start = date
            self.left_calendar.title.set_named_date_text(date)
        else:
            Dynamic.date_end = date
            self.right_calendar.title.set_named_date_text(date)

        if all((Dynamic.date_start, Dynamic.date_end)):
            Dynamic.f_date_start = self.named_date(Dynamic.date_start)
            Dynamic.f_date_end = self.named_date(Dynamic.date_end)
            self.reload_thumbnails.emit()
            self.dates_btn_solid.emit()
    
    def named_date(self, date: datetime) -> str:
        return date.strftime("%d.%m.%Y")
    
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
        return super().keyPressEvent(a0)
