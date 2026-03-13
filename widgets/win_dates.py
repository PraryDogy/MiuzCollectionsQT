import calendar
import re
from datetime import datetime, timedelta
from typing import Literal

from PyQt5.QtCore import QDate, QLocale, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QKeyEvent
from PyQt5.QtWidgets import (QCalendarWidget, QFrame, QGroupBox, QLabel,
                             QLineEdit, QSpacerItem, QSpinBox, QToolButton,
                             QVBoxLayout, QWidget)

from cfg import Dynamic, Cfg
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
        super().__init__()
        self.default_text = default_text
        self.setText(default_text)

    def set_named_date_text(self, date: datetime):
        weekday = self.get_named_weekday(date)
        named_date = self.get_named_date(date)
        text = f"{named_date}, {weekday}"
        self.setText(text)

    def set_default_text(self):
        self.setText(self.default_text)

    def get_named_weekday(self, date: datetime) -> str:
        day_number = str(date.weekday())
        return Lng.weekdays_short[Cfg.lng][day_number]
    
    def get_named_date(self, date: datetime) -> str:
        month_number = str(date.month)
        month = Lng.months_genitive_case[Cfg.lng][month_number]
        return f"{date.day} {month} {date.year}"
    
    def setText(self, a0):
        a0 = " " + a0
        return super().setText(a0)


class MyCalendar(QGroupBox):
    dateSelected = pyqtSignal(QDate)

    def __init__(self, title: str):
        super().__init__()
        v_layout = UVBoxLayout(self)
        v_layout.setSpacing(10)
        margins = v_layout.contentsMargins()
        margins.setTop(5)
        v_layout.setContentsMargins(margins)

        self.title = DatesTitle(title)
        v_layout.addWidget(self.title)

        self.calendar = QCalendarWidget()
        self.calendar.setMaximumDate(QDate.currentDate())
        self.calendar.setMinimumDate(QDate(2000, 1, 1))
        self.calendar.setFixedSize(300, 300)
        v_layout.addWidget(self.calendar)
        if Cfg.lng == 0:
            self.calendar.setLocale(QLocale(QLocale.Language.Russian))
        else:
            self.calendar.setLocale(QLocale(QLocale.Language.English))
        self.calendar.clicked.connect(self.on_date_clicked)
        self.set_custom_ui()

    def on_date_clicked(self, date: QDate):
        self.dateSelected.emit(date)

    def set_date(self, py_date: datetime):
        qdate = QDate(py_date.year, py_date.month, py_date.day)
        self.calendar.setSelectedDate(qdate)

    def set_custom_ui(self, icon_size: int = 10):
        self.calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )

        widgets = self.findChildren(QToolButton)
        for wid in widgets:
            name = wid.objectName()
            if name == "qt_calendar_prevmonth":
                wid.setIcon(QIcon("./images/prev.svg"))
            elif name == "qt_calendar_nextmonth":
                wid.setIcon(QIcon("./images/next.svg"))

        self.calendar.setStyleSheet("""
            #qt_calendar_monthbutton::menu-indicator {
                image: none;
                width: 0px;
            }

            #qt_calendar_prevmonth,
            #qt_calendar_nextmonth,
            #qt_calendar_monthbutton,
            #qt_calendar_yearbutton {
                height: 25px;
                background: transparent;                                 
            }

            #qt_calendar_prevmonth,
            #qt_calendar_nextmont {
                width: 25px;
            }

            #qt_calendar_prevmonth:hover,
            #qt_calendar_nextmonth:hover,
            #qt_calendar_monthbutton:hover,
            #qt_calendar_yearbutton:hover {                  
                background: transparent;  
                border: transparent;
                color: white;                                 
            }
        """)


class WinDates(SingleActionWindow):
    dates_btn_solid = pyqtSignal()
    dates_btn_normal = pyqtSignal()
    reload_thumbnails = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lng.search_dates[Cfg.lng])

        self.central_layout.setSpacing(10)
        self.central_layout.setContentsMargins(10, 10, 10, 10)

        dates_h_wid = QWidget()
        self.central_layout.addWidget(dates_h_wid)
        dates_h_lay = UHBoxLayout()
        dates_h_lay.setSpacing(10)
        dates_h_wid.setLayout(dates_h_lay)

        self.left_calendar = MyCalendar(Lng.start_date[Cfg.lng])
        self.left_calendar.dateSelected.connect(
            lambda date: self.date_change(date=date, flag="start")
        )
        dates_h_lay.addWidget(self.left_calendar)

        self.right_calendar = MyCalendar(Lng.end_date[Cfg.lng])
        self.right_calendar.dateSelected.connect(
            lambda date: self.date_change(date=date, flag="end")
        )
        dates_h_lay.addWidget(self.right_calendar)

        self.central_layout.addWidget(HSep())

        clear_btn = SmallBtn(text=Lng.reset[Cfg.lng])
        clear_btn.setFixedWidth(100)
        clear_btn.clicked.connect(self.clear_btn_cmd)
        self.central_layout.addWidget(
            clear_btn,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        m = self.central_layout.contentsMargins()
        m.setBottom(15)
        self.central_layout.setContentsMargins(m)

        self.adjustSize()

        if Dynamic.date_start:
            self.left_calendar.set_date(Dynamic.date_start)
            self.left_calendar.title.set_named_date_text(Dynamic.date_start)
        if Dynamic.date_end:
            self.right_calendar.set_date(Dynamic.date_end)
            self.right_calendar.title.set_named_date_text(Dynamic.date_end)

    def clear_btn_cmd(self, *args):
        reload = True
        if not Dynamic.date_start or not Dynamic.date_end:
            reload = False
        Dynamic.loaded_thumbs = 0
        Dynamic.date_start = None
        Dynamic.date_end = None
        Dynamic.f_date_start = None
        Dynamic.f_date_end = None
        if reload:
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
            self.left_calendar.calendar.setMaximumDate(
                QDate(date.year, date.month, date.day)
            )

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
