import os
import sys
from datetime import date

from PyQt6.QtCore import QDate, QLocale, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QMouseEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QMenu,
                             QPushButton, QWidget)

from cfg import Static
from widgets._base_widgets import UMainWidget, UPushButton


class BigDateLabel(QLabel):

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setText("30 сентября 2026") 
        self.adjustSize() 
        self.setFixedWidth(self.width())
        self.setText("") 


class ClickableSvgWidget(QSvgWidget):
    # Создаем сигнал, который будет срабатывать при клике
    clicked = pyqtSignal()

    def __init__(self, file_path, parent=None):
        super().__init__(file_path, parent)
        # Устанавливаем курсор в виде руки при наведении
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        # Проверяем, что кликнули именно левой кнопкой мыши
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)


# Кастомный кликабельный QLabel для дней
class ClickableLabel(QLabel):
    def __init__(self, text, day_num, parent=None):
        super().__init__(text, parent)
        self.day_num = day_num

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Получаем родительский календарь и вызываем выбор дня
            calendar = self.window()
            if hasattr(calendar, "day_selected"):
                calendar.day_selected(self.day_num)
        super().mousePressEvent(event)


class CustomCalendar(UMainWidget):
    svg_calendar = os.path.join(Static.common_icons, "calendar.svg")
    svg_previous = os.path.join(Static.common_icons, "previous.svg")
    svg_next = os.path.join(Static.common_icons, "next.svg")

    row_height = 40
    cell_size = (40, 40)
    svg_nav = (20, 20)
    svg_calendar_size = (30, 30)
    grid_h_spacing = 15
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

    def init_ui(self):
        self.central_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        dynamic_container = QWidget()
        self.central_layout.addWidget(dynamic_container)
        dynamic_container_lay = QHBoxLayout(dynamic_container)
        dynamic_container_lay.setContentsMargins(0, 0, 0, 0)
        dynamic_container_lay.setSpacing(15)

        dynamic_container_lay.addSpacing(5)

        calendar_icon = QSvgWidget()
        calendar_icon.load(self.svg_calendar)
        calendar_icon.setFixedSize(*self.svg_calendar_size)
        dynamic_container_lay.addWidget(calendar_icon)

        self.dynamic_label = BigDateLabel()
        dynamic_container_lay.addWidget(self.dynamic_label)

        dynamic_container_lay.addStretch()

        # --- Первая строка: Панель навигации ---
        self.nav_widget = QWidget()
        self.nav_widget.setFixedHeight(self.row_height)
        self.nav_layout = QHBoxLayout(self.nav_widget)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(5)
    
        self.btn_prev = ClickableSvgWidget(self.svg_previous)
        self.btn_prev.setFixedSize(*self.svg_nav)
        self.btn_prev.clicked.connect(self.prev_month)
        
        # Убираем fixedWidth, чтобы кнопки подстраивались под новую ширину
        self.btn_month = UPushButton("")
        self.menu_month = QMenu(self)
        self.btn_month.setMenu(self.menu_month)
        self.populate_months()

        self.btn_year = UPushButton("")
        self.menu_year = QMenu(self)
        self.btn_year.setMenu(self.menu_year)
        self.populate_years()
        
        self.btn_next = ClickableSvgWidget(self.svg_next)
        self.btn_next.setFixedSize(*self.svg_nav)
        self.btn_next.clicked.connect(self.next_month)
        
        # Распределяем верхние кнопки по ширине широкого календаря
        self.nav_layout.addSpacing(10)
        self.nav_layout.addWidget(self.btn_prev)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.btn_month)
        self.nav_layout.addWidget(self.btn_year)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.btn_next)
        self.nav_layout.addSpacing(10)
        
        self.central_layout.addWidget(self.nav_widget)

        # --- Сетка для дней недели и чисел ---
        self.grid_widget = QWidget()  
        
        # Точный пересчет максимальной высоты с учетом раздельных отступов (7 строк и 6 вертикальных промежутков)
        max_grid_height = (7 * self.cell_size[0]) + (6 * self.grid_v_spacing)
        self.grid_widget.setFixedHeight(max_grid_height)
        
        self.grid_layout = QGridLayout(self.grid_widget)  
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # --- РАЗДЕЛЯЕМ ОТСТУПЫ ---
        self.grid_layout.setHorizontalSpacing(self.grid_h_spacing) # Растягивает по горизонтали
        self.grid_layout.setVerticalSpacing(self.grid_v_spacing)     # Сохраняет компактность по вертикали
        
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

    def populate_years(self, start_year: int = 2015):
        self.menu_year.clear()
        max_year = QDate.currentDate().year()
        for y in range(start_year, max_year + 1):
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
        min_date = QDate(2015, 1, 1)
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

    def update_calendar(self):
        self.update_dynamic_label()
        current_year = self.current_date.year()
        current_month = self.current_date.month()

        current_month_name = self.q_locale.standaloneMonthName(current_month, QLocale.FormatType.LongFormat)
        self.btn_month.setText(current_month_name.capitalize())
        self.btn_year.setText(str(current_year))
        
        # Проверка доступности стрелок по лимитам дат (2015.01.01 ... текущий_год.12.31)
        self.btn_prev.setEnabled(not (current_year == 2015 and current_month == 1))
        
        max_year = QDate.currentDate().year()
        self.btn_next.setEnabled(not (current_year == max_year and current_month == 12))

        self.clear_grid()

        # Рендеринг дней недели
        for col in range(7):
            day_of_week = col + 1 
            day_name = self.q_locale.dayName(day_of_week, QLocale.FormatType.ShortFormat).capitalize()
            lbl_day = QLabel(day_name)
            lbl_day.setObjectName("weekday") 
            lbl_day.setFixedSize(*self.cell_size)
            lbl_day.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(lbl_day, 0, col)

        # Рендеринг чисел месяца
        first_day_of_month = QDate(current_year, current_month, 1)
        start_col = first_day_of_month.dayOfWeek() - 1 
        
        days_in_month = self.current_date.daysInMonth()
        selected_day = self.current_date.day() 

        current_day = 1
        row = 1
        col = start_col

        while current_day <= days_in_month:
            # Используем кастомный кликабельный QLabel вместо обычного
            btn_day = ClickableLabel(str(current_day), current_day)
            btn_day.setFixedSize(*self.cell_size)
            btn_day.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if current_day == selected_day:
                btn_day.setObjectName("day_selected")
            else:
                btn_day.setObjectName("day_regular")
                
            btn_day.style().unpolish(btn_day)
            
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