import os
import sys
from datetime import datetime, timedelta
from typing import Literal

from PyQt6.QtCore import QDate, QLocale, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (QAction, QBrush, QColor, QIcon, QKeyEvent,
                         QTextCharFormat)
from PyQt6.QtWidgets import (QApplication, QCalendarWidget, QComboBox,
                             QDateEdit, QDialog, QGroupBox, QHBoxLayout,
                             QLabel, QMainWindow, QPushButton, QSpinBox,
                             QToolButton, QVBoxLayout, QWidget)

from cfg import Dynamic, JsonData, Static
from system.lang import Lng

from ._base_widgets import HSep, UMainWidget, UMenu, UPushButton


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
        return Lng.weekdays_short[JsonData.lng_index][day_number]
    
    def get_named_date(self, date: datetime) -> str:
        month_number = str(date.month)
        month = Lng.months_gen[JsonData.lng_index][month_number]
        return f"{date.day} {month} {date.year}"
    
    def setText(self, a0):
        a0 = " " + a0
        return super().setText(a0)


class MyCalendar(QGroupBox):
    dateSelected = pyqtSignal(QDate)

    def __init__(self, title: str):
        super().__init__()
        v_layout = QVBoxLayout(self)
        v_layout.setContentsMargins(0, 0, 0, 0)
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
        if JsonData.lng_index == 0:
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

    def set_custom_ui(self, icon_size: int = 17):
        self.calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )

        widgets = self.findChildren(QToolButton)
        for wid in widgets:
            name = wid.objectName()
            wid.setIconSize(QSize(icon_size, icon_size))
            if name == "qt_calendar_prevmonth":
                wid.setIcon(QIcon(os.path.join(Static.common_icons, "previous.svg")))
            elif name == "qt_calendar_nextmonth":
                wid.setIcon(QIcon(os.path.join(Static.common_icons, "next.svg")))


        for child in self.calendar.findChildren(QSpinBox):
            child.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

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


class WinDates(UMainWidget):
    dates_btn_solid = pyqtSignal()
    dates_btn_normal = pyqtSignal()
    reload_thumbnails = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.search_dates[JsonData.lng_index])

        preset_widget = QWidget()
        self.central_layout.addWidget(preset_widget)
        preset_layout = QHBoxLayout(preset_widget)
        preset_layout.setContentsMargins(0, 0, 0, 0)
        preset_layout.setSpacing(0)

        period_label = QLabel("Период")
        preset_layout.addWidget(period_label)


        self.preset_button = UPushButton("")
        self.preset_button.setFixedWidth(120)
        preset_layout.addWidget(self.preset_button)

        preset_menu = UMenu(None)
        self.preset_button.setMenu(preset_menu)

        self.preset_actions = [
            QAction("Все время", preset_menu),
            QAction("Сегодня", preset_menu),
            QAction("За неделю", preset_menu),
            QAction("За месяц", preset_menu),
            QAction("За год", preset_menu),
            QAction("Диапазон", preset_menu),
        ]

        for x, act in enumerate(self.preset_actions, start=0):
            act.triggered.connect(
                lambda e, ind=x, act=act: self.action_cmd(e, ind, act)
            )
            preset_menu.addAction(act)
        
        date_layout = QHBoxLayout()
        self.central_layout.addLayout(date_layout)
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        date_layout.addWidget(self.date_from)

        self.date_to = QDateEdit(QDate.currentDate())
        date_layout.addWidget(self.date_to)

        for widget in [self.date_from, self.date_to]:
            widget.setCalendarPopup(True) # Встроенный выпадающий календарь
            widget.setEnabled(False)      # По умолчанию заблокирован

        from_label = QLabel("С:")
        date_layout.addWidget(from_label)

        to_label = QLabel("По:")
        date_layout.addWidget(to_label)
        
        self.apply_btn = UPushButton(Lng.reset[JsonData.lng_index])
        self.apply_btn.clicked.connect(
            lambda index=0: self.handle_preset_change(index)
        )
        self.apply_btn.clicked.connect(
            lambda: self.apply_filter()
        )
        self.apply_btn.clicked.connect(self.apply_filter)
        self.central_layout.addWidget(self.apply_btn)

        self.adjustSize()

    def action_cmd(self, e, index: int, action: QAction):
        self.preset_button.setText(action.text())
        self.handle_preset_change(index)
        self.apply_filter()
        
    def handle_preset_change(self, index):
        is_custom = (index == len(self.preset_actions) - 1)
        self.date_from.setEnabled(is_custom)
        self.date_to.setEnabled(is_custom)
        
        today = QDate.currentDate()
        if not is_custom:
            self.date_to.setDate(today)
            if index == 0:   # Все время
                self.date_from.setDate(QDate(1970, 1, 1)) # Или любая минимальная дата вашей галереи
            elif index == 1: # Сегодня
                self.date_from.setDate(today)
            elif index == 2: # За неделю
                self.date_from.setDate(today.addDays(-7))
            elif index == 3: # За месяц
                self.date_from.setDate(today.addMonths(-1))
            elif index == 4: # За year
                self.date_from.setDate(today.addYears(-1))

    def apply_filter(self):
        Dynamic.date_start = self.date_from.date().toPyDate()
        Dynamic.date_end = self.date_to.date().toPyDate()
        self.reload_thumbnails.emit()
        self.dates_btn_solid.emit()

    def clear_btn_cmd(self, *args):
        reload = True
        if not Dynamic.date_start or not Dynamic.date_end:
            reload = False
        Dynamic.loaded_thumbs = 0
        Dynamic.date_start = None
        Dynamic.date_end = None
        if reload:
            self.reload_thumbnails.emit()
            self.dates_btn_normal.emit()
            self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)