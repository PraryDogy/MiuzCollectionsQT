import os
import sys
from datetime import date

from PyQt6.QtCore import QDate, QLocale, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QMouseEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                             QMenu, QPushButton, QWidget, QVBoxLayout)

from cfg import Static

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

    def __init__(self, text: str):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        return super().mouseReleaseEvent(ev)


class CalendarDay(CalendarDayBase):
    def __init__(self, text):
        super().__init__(text)


class CalendarDaySelected(CalendarDayBase):
    def __init__(self, text):
        super().__init__(text)


class CalendarWeek(CalendarDayBase):
    def __init__(self, text: str):
        super().__init__(text)


class Calendar(UMainWidget):
    svg_calendar = os.path.join(Static.common_icons, "calendar.svg")
    svg_previous = os.path.join(Static.common_icons, "previous.svg")
    svg_next = os.path.join(Static.common_icons, "next.svg")

    min_year = 2015

    cell_size = (40, 40)
    svg_nav = (20, 20)
    svg_calendar_size = (25, 25)
    grid_h_spacing = 25
    grid_v_spacing = 5

    def __init__(self, date_val: QDate = QDate.currentDate()):
        super().__init__()
        self.q_locale = QLocale(QLocale.Language.Russian, QLocale.Country.Russia)
        
        self.current_date = date_val
        
        self.setWindowTitle("Кастомный Календарь")
        self.set_close_only()
        self.set_always_on_top()
        self.init_ui()
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())
        self.central_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def init_ui(self):
        # Большая дата (теперь на обычном QWidget вместо QGroupBox)
        dynamic_container = QWidget()
        self.central_layout.addWidget(dynamic_container)
        dynamic_container_lay = QHBoxLayout(dynamic_container)
        dynamic_container_lay.setContentsMargins(0, 0, 0, 5)

        dynamic_container_lay.addSpacing(5)

        calendar_icon = QSvgWidget()
        calendar_icon.load(self.svg_calendar)
        calendar_icon.setFixedSize(*self.svg_calendar_size)
        dynamic_container_lay.addWidget(calendar_icon)

        self.dynamic_label = CalendarBigDate()
        dynamic_container_lay.addWidget(self.dynamic_label)

        dynamic_container_lay.addStretch()

        # Календарь навигация
        self.nav_widget = QWidget()
        self.nav_widget.setFixedHeight(self.cell_size[0])
        self.nav_layout = QHBoxLayout(self.nav_widget)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(5)

        self.btn_prev = CalendarSvgNavi(self.svg_previous)
        self.btn_prev.setFixedSize(*self.svg_nav)
        self.btn_prev.clicked.connect(self.prev_month)
        
        self.btn_month = UPushButton("")
        self.menu_month = QMenu(self)
        self.btn_month.setMenu(self.menu_month)
        self.populate_months()

        self.btn_year = UPushButton("")
        self.menu_year = QMenu(self)
        self.btn_year.setMenu(self.menu_year)
        self.populate_years()
        
        self.btn_next = CalendarSvgNavi(self.svg_next)
        self.btn_next.setFixedSize(*self.svg_nav)
        self.btn_next.clicked.connect(self.next_month)
        
        self.nav_layout.addSpacing(10)
        self.nav_layout.addWidget(self.btn_prev)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.btn_month)
        self.nav_layout.addWidget(self.btn_year)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.btn_next)
        self.nav_layout.addSpacing(10)
        
        # Добавляем навигацию напрямую в главный макет
        self.central_layout.addWidget(self.nav_widget)

        # --- Сетка для дней недели и чисел ---
        self.grid_widget = QWidget()  
        
        self.grid_layout = QGridLayout(self.grid_widget)  
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.grid_layout.setHorizontalSpacing(self.grid_h_spacing)
        self.grid_layout.setVerticalSpacing(self.grid_v_spacing)
        
        # Добавляем сетку напрямую в главный макет
        self.central_layout.addWidget(self.grid_widget)


        
        self.update_calendar()

    def update_dynamic_label(self):
        russian_locale = QLocale(QLocale.Language.Russian, QLocale.Country.Russia)
        readable_date = russian_locale.toString(self.current_date, "d MMMM yyyy")
        self.dynamic_label.setText(readable_date)

    def populate_months(self):
        self.menu_month.clear()
        for m in range(1, 13):
            month_name = self.q_locale.standaloneMonthName(m, QLocale.FormatType.LongFormat).capitalize()
            action = QAction(month_name, self)
            action.setData(m)
            action.triggered.connect(self.month_menu_selected)
            self.menu_month.addAction(action)

    def populate_years(self):
        self.menu_year.clear()
        max_year = QDate.currentDate().year()
        for y in range(self.min_year, max_year + 1):
            action = QAction(str(y), self)
            action.setData(y)
            action.triggered.connect(self.year_menu_selected)
            self.menu_year.addAction(action)

    def month_menu_selected(self):
        action = self.sender()
        if action:
            selected_month = action.data()
            target_day = min(self.current_date.day(), QDate(self.current_date.year(), selected_month, 1).daysInMonth())
            self.current_date = QDate(self.current_date.year(), selected_month, target_day)
            self.update_calendar()

    def year_menu_selected(self):
        action = self.sender()
        if action:
            selected_year = action.data()
            target_day = min(self.current_date.day(), QDate(selected_year, self.current_date.month(), 1).daysInMonth())
            self.current_date = QDate(selected_year, self.current_date.month(), target_day)
            self.update_calendar()

    # Смена дня при клике на сетку чисел
    def day_selected(self, day_num: int):
        self.current_date = QDate(self.current_date.year(), self.current_date.month(), day_num)
        self.update_calendar()

    # Стрелки теперь листают месяцы вперед/назад с сохранением лимитов по годам
    def prev_month(self):
        min_date = QDate(self.min_year, 1, 1)
        new_date = self.current_date.addMonths(-1)
        if new_date >= min_date:
            self.current_date = new_date
            self.update_calendar()

    def next_month(self):
        max_date = QDate(QDate.currentDate().year(), 12, 31)
        new_date = self.current_date.addMonths(1)
        if new_date <= max_date:
            self.current_date = new_date
            self.update_calendar()

    def clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def day_clicked(self, day: int):
        new_date = QDate(self.current_date.year(), self.current_date.month(), day)
        self.current_date = new_date
        self.update_calendar()

    def update_calendar(self):
        self.update_dynamic_label()
        current_year = self.current_date.year()
        current_month = self.current_date.month()
        current_month_name = self.q_locale.standaloneMonthName(
            current_month,
            QLocale.FormatType.LongFormat
        )
        self.btn_month.setText(current_month_name.capitalize())
        self.btn_year.setText(str(current_year))
        if current_year == self.min_year and current_month == 1:
            self.btn_prev.set_disabled()
        else:
            self.btn_prev.set_enabled()
        
        max_year = QDate.currentDate().year()
        if current_year == max_year and current_month == 12:
            self.btn_next.set_disabled()
        else:
            self.btn_next.set_enabled()

        self.clear_grid()

        for col in range(7):
            day_of_week = col + 1 
            day_name = self.q_locale.dayName(day_of_week, QLocale.FormatType.ShortFormat).capitalize()
            lbl_day = CalendarWeek(day_name)
            lbl_day.setFixedSize(*self.cell_size)
            self.grid_layout.addWidget(lbl_day, 0, col)

        first_day_of_month = QDate(current_year, current_month, 1)
        start_col = first_day_of_month.dayOfWeek() - 1 
        days_in_month = self.current_date.daysInMonth()
        selected_day = self.current_date.day() 
        current_day = 1
        row = 1
        col = start_col

        while current_day <= days_in_month:
            if current_day == selected_day:
                btn_day = CalendarDaySelected(str(current_day))
            else:
                btn_day = CalendarDay(str(current_day))
            btn_day.clicked.connect(
                lambda d=current_day: self.day_clicked(d)
            )

            btn_day.setFixedSize(*self.cell_size)
            self.grid_layout.addWidget(btn_day, row, col)
            col += 1
            if col > 6:
                col = 0
                row += 1
            current_day += 1

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)