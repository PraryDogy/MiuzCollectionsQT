import os
import sys
from datetime import date

from PyQt6.QtCore import QDate, QLocale, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QMouseEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                             QMenu, QPushButton, QVBoxLayout, QWidget)

from cfg import JsonData, Static
from system.lang import Lng

from ._base_widgets import HSep, UMainWidget, UPushButton


class CalendarBigDate(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setText("30 сентября 2026") 
        self.adjustSize() 
        self.setFixedWidth(self.width())
        self.clear()


class CalendarSvgNavi(QSvgWidget):
    clicked = pyqtSignal()

    def __init__(self, file_path, parent=None):
        super().__init__(file_path, parent)
        self._is_active = True
        self.set_enabled()

    def set_enabled(self):
        self._is_active = True
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_disabled(self):
        self._is_active = False
        self.setCursor(Qt.CursorShape.ForbiddenCursor)

    def mouseReleaseEvent(self, a0):
        # Если флаг False, клик просто игнорируется
        if self._is_active and a0.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        return super().mouseReleaseEvent(a0)


class CalendarDayBase(QLabel):
    clicked = pyqtSignal()
    def __init__(self, text: str, day: int):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.day: int = day

    def mouseReleaseEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        return super().mouseReleaseEvent(ev)

    
class CalendarDay(CalendarDayBase):
    def __init__(self, text: str, day: int):
        super().__init__(text, day)


class CalendarDaySelected(CalendarDayBase):
    def __init__(self, text: str, day: int):
        super().__init__(text, day)


class CalendarWeek(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class CalendarSep(HSep):
    def __init__(self, margin: int):
        super().__init__()
        self.setStyleSheet(
            f"""
                margin-left: {margin}px;
                margin-right: {margin}px;
            """
        )


class Calendar(UMainWidget):
    svg_calendar = Static.COMMON_ICONS / "calendar.svg"
    svg_previous = Static.COMMON_ICONS / "previous.svg"
    svg_next = Static.COMMON_ICONS / "next.svg"

    min_year = 2015
    day_property = "day_value"

    cell_size = (40, 40)
    svg_nav = (20, 20)
    svg_calendar_size = (25, 25)
    grid_h_spacing = 25
    grid_v_spacing = 5

    def __init__(self, date: QDate):
        super().__init__()

        if JsonData.lng_index == 0:
            lng = QLocale.Language.Russian
            country = QLocale.Country.Russia
        else:
            lng = QLocale.Language.English
            country = QLocale.Country.UnitedStates

        self.q_locale = QLocale(lng, country)
        self.current_date = date
        self.date_now = QDate.currentDate()
        
        self.setWindowTitle(Lng.calendar[JsonData.lng_index])
        self.set_close_only()
        self.set_always_on_top()
        self.init_ui()
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())
        self.central_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def init_ui(self):

        margin = 10

        # --- 1. Блок большой даты ---
        dynamic_container = QWidget()
        self.central_layout.addWidget(dynamic_container) # Добавляем сразу
        
        dynamic_container_lay = QHBoxLayout(dynamic_container)
        dynamic_container_lay.setContentsMargins(margin, 0, margin, 0)
        dynamic_container_lay.setSpacing(0)

        calendar_icon = QSvgWidget()
        calendar_icon.load(str(self.svg_calendar))
        calendar_icon.setFixedSize(*self.svg_calendar_size)
        dynamic_container_lay.addWidget(calendar_icon)

        dynamic_container_lay.addSpacing(10)

        self.dynamic_label = CalendarBigDate()
        dynamic_container_lay.addWidget(self.dynamic_label)
        dynamic_container_lay.addStretch()

        # --- Разделитель ---
        self.central_layout.addSpacing(5)

        sep = CalendarSep(margin)
        self.central_layout.addWidget(sep)

        # --- 2. Блок навигации календаря ---
        self.nav_widget = QWidget()
        self.nav_widget.setFixedHeight(self.cell_size[0])
        self.central_layout.addWidget(self.nav_widget) # Добавляем сразу
        
        self.nav_layout = QHBoxLayout(self.nav_widget)
        self.nav_layout.setContentsMargins(margin, 0, margin, 0)
        self.nav_layout.setSpacing(0)

        self.btn_prev = CalendarSvgNavi(str(self.svg_previous))
        self.btn_prev.setFixedSize(*self.svg_nav)
        self.btn_prev.clicked.connect(self.prev_month)
        self.nav_layout.addWidget(self.btn_prev)

        self.nav_layout.addStretch()
        
        self.btn_month = UPushButton("")
        self.menu_month = QMenu(self)
        self.btn_month.setMenu(self.menu_month)
        self.populate_months()
        self.nav_layout.addWidget(self.btn_month)

        self.nav_layout.addSpacing(10)

        self.btn_year = UPushButton("")
        self.menu_year = QMenu(self)
        self.btn_year.setMenu(self.menu_year)
        self.populate_years()
        self.nav_layout.addWidget(self.btn_year)

        self.nav_layout.addStretch()
        
        self.btn_next = CalendarSvgNavi(str(self.svg_next))
        self.btn_next.setFixedSize(*self.svg_nav)
        self.btn_next.clicked.connect(self.next_month)
        self.nav_layout.addWidget(self.btn_next)

        # sep = CalendarSep(margin)
        # self.central_layout.addWidget(sep)

        # --- 3. Сетка для дней недели и чисел ---
        self.grid_widget = QWidget()  
        self.central_layout.addWidget(self.grid_widget) # Добавляем сразу
        
        self.grid_layout = QGridLayout(self.grid_widget)  
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid_layout.setHorizontalSpacing(self.grid_h_spacing)
        self.grid_layout.setVerticalSpacing(self.grid_v_spacing)
        
        self.update_calendar()

    def update_dynamic_label(self):        
        readable_date = self.q_locale.toString(
            self.current_date,
            "d MMMM yyyy"
        )
        self.dynamic_label.setText(readable_date)

    def populate_months(self):
        self.menu_month.clear()
        for month in range(1, 13):
            month_name = self.q_locale.standaloneMonthName(
                month,
                QLocale.FormatType.LongFormat
            )
            action = QAction(month_name.capitalize(), self)
            action.setData(month)
            action.triggered.connect(self.month_menu_selected)
            self.menu_month.addAction(action)

    def populate_years(self):
        self.menu_year.clear()
        max_year = self.date_now.year()
        for year in range(self.min_year, max_year + 1):
            action = QAction(str(year), self)
            action.setData(year)
            action.triggered.connect(self.year_menu_selected)
            self.menu_year.addAction(action)

    def month_menu_selected(self):
        action: QAction = self.sender()
        selected_month = action.data()
        year = self.current_date.year()
        current_day = self.current_date.day()
        # 1. Узнаем, сколько всего дней в выбранном месяце
        days_in_new_month = QDate(year, selected_month, 1).daysInMonth()
        # 2. Если текущий день больше, чем дней в новом месяце, берем максимум для этого месяца
        if current_day > days_in_new_month:
            target_day = days_in_new_month
        else:
            target_day = current_day
        self.current_date = QDate(year, selected_month, target_day)
        self.update_calendar()

    def year_menu_selected(self):
        action: QAction = self.sender()
        selected_year = action.data()
        current_month = self.current_date.month()
        current_day = self.current_date.day()
        days_in_new_month = QDate(selected_year, current_month, 1).daysInMonth()
        if current_day > days_in_new_month:
            target_day = days_in_new_month
        else:
            target_day = current_day
        self.current_date = QDate(selected_year, current_month, target_day)
        self.update_calendar()

    def day_selected(self):
        sender_button: CalendarDayBase = self.sender()
        day = sender_button.day
        current_year = self.current_date.year()
        current_month = self.current_date.month()
        self.current_date = QDate(current_year, current_month, day)
        self.update_calendar()

    def prev_month(self):
        min_date = QDate(self.min_year, 1, 1)
        new_date = self.current_date.addMonths(-1)
        if new_date >= min_date:
            self.current_date = new_date
            self.update_calendar()

    def next_month(self):
        max_date = QDate(self.date_now.year(), 12, 31)
        new_date = self.current_date.addMonths(1)
        if new_date <= max_date:
            self.current_date = new_date
            self.update_calendar()

    def clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def update_calendar(self):
        self.update_dynamic_label()
        current_year = self.current_date.year()
        current_month = self.current_date.month()
        current_day_val = self.current_date.day()
        month = self.q_locale.standaloneMonthName(
            current_month,
            QLocale.FormatType.LongFormat
        )
        self.btn_month.setText(month.capitalize())
        self.btn_year.setText(str(current_year))
        if current_year == self.min_year and current_month == 1:
            self.btn_prev.set_disabled()
        else:
            self.btn_prev.set_enabled()
        if current_year == QDate.currentDate().year() and current_month == 12:
            self.btn_next.set_disabled()
        else:
            self.btn_next.set_enabled()
        self.clear_grid()
        for col in range(7):
            week = self.q_locale.dayName(col + 1, QLocale.FormatType.ShortFormat)
            lbl_day = CalendarWeek(week.capitalize())
            lbl_day.setFixedSize(*self.cell_size)
            self.grid_layout.addWidget(lbl_day, 0, col)
        first_day = QDate(current_year, current_month, 1)
        # Находим индекс колонки (0-6) для первого дня месяца, чтобы учесть смещение в сетке
        start_col = first_day.dayOfWeek() - 1
        days_in_month = first_day.daysInMonth()
        for day in range(1, days_in_month + 1):
            if day == current_day_val:
                btn_day = CalendarDaySelected(str(day), day)
            else:
                btn_day = CalendarDay(str(day), day)
            btn_day.setFixedSize(*self.cell_size)
            btn_day.clicked.connect(self.day_selected)
            # divmod вычисляет номер строки и колонки на основе сквозного индекса ячейки
            row, col = divmod(start_col + day - 1, 7)
            # Смещаем строку на +1, так как нулевую строку (row=0) занимают названия дней недели
            self.grid_layout.addWidget(btn_day, row + 1, col)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)