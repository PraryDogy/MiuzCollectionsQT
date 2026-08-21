import sys
from datetime import date

from PyQt6.QtCore import QLocale, Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QMenu, QWidget

from widgets._base_widgets import UMainWidget, UPushButton


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


class MonthYearBtn(UPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setFixedWidth(90)


class CustomCalendar(UMainWidget):
    def __init__(self):
        super().__init__()
        self.q_locale = QLocale(QLocale.Language.Russian, QLocale.Country.Russia)
        self.current_date = date.today()
        self.row_height = 30
        self.setWindowTitle("Кастомный Календарь")
        self.set_close_only()
        self.set_always_on_top()
        self.init_ui()
        self.adjustSize()

    def init_ui(self):
        # --- Первая строка: Панель навигации (Контейнер) ---
        self.nav_widget = QWidget()
        self.nav_widget.setFixedHeight(self.row_height)
        self.nav_layout = QHBoxLayout(self.nav_widget)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(0)
        
        # Стрелка влево (Предыдущий год)
        self.btn_prev = ClickableSvgWidget("./icons/common/previous.svg")
        self.btn_prev.setFixedSize(16, 16)
        self.btn_prev.clicked.connect(self.prev_year)
        
        # Кнопка выбора месяца с QMenu
        self.btn_month = MonthYearBtn("")
        self.menu_month = QMenu(self)
        self.btn_month.setMenu(self.menu_month)
        self.populate_months()

        # Кнопка выбора года с QMenu
        self.btn_year = MonthYearBtn("")
        self.menu_year = QMenu(self)
        self.btn_year.setMenu(self.menu_year)
        self.populate_years()
        
        # Стрелка вправо (Следующий год)
        self.btn_next = ClickableSvgWidget("./icons/common/next.svg")
        self.btn_next.setFixedSize(16, 16)
        self.btn_next.clicked.connect(self.next_year)
        
        # Собираем навигационную панель внутри контейнера
        self.nav_layout.addWidget(self.btn_prev)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.btn_month)
        self.nav_layout.addSpacing(5)
        self.nav_layout.addWidget(self.btn_year)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.btn_next)
        
        # Добавляем контейнер навигации как виджет
        self.central_layout.addWidget(self.nav_widget)

        # --- Сетка для дней недели и чисел (Контейнер) ---
        self.grid_widget = QWidget()  # Создаем виджет-контейнер для сетки
        self.grid_layout = QGridLayout(self.grid_widget)  # Привязываем сетку к виджету
        self.grid_layout.setSpacing(5)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Добавляем контейнер сетки как виджет
        self.central_layout.addWidget(self.grid_widget)
        
        # Обновляем интерфейс под текущую дату
        self.update_calendar()
        # self.adjustSize()

    def populate_months(self):
        self.menu_month.clear()
        for m in range(1, 13):
            month_name = self.q_locale.standaloneMonthName(m, QLocale.FormatType.LongFormat).capitalize()
            action = QAction(month_name, self)
            action.setData(m)
            action.triggered.connect(self.month_selected)
            self.menu_month.addAction(action)

    def populate_years(self, start_year: int = 2015):
        self.menu_year.clear()
        max_year = date.today().year
        for y in range(start_year, max_year + 1):
            action = QAction(str(y), self)
            action.setData(y)
            action.triggered.connect(self.year_selected)
            self.menu_year.addAction(action)

    def month_selected(self):
        action = self.sender()
        if action:
            selected_month = action.data()
            self.current_date = self.current_date.replace(month=selected_month)
            self.update_calendar()

    def year_selected(self):
        action = self.sender()
        if action:
            selected_year = action.data()
            self.current_date = self.current_date.replace(year=selected_year)
            self.update_calendar()

    def prev_year(self):
        if self.current_date.year > 2015:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1)
            self.update_calendar()

    def next_year(self):
        max_year = date.today().year
        if self.current_date.year < max_year:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1)
            self.update_calendar()

    def clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def update_calendar(self):
        current_month_name = self.q_locale.standaloneMonthName(
            self.current_date.month,
            QLocale.FormatType.LongFormat
        )
        self.btn_month.setText(current_month_name.capitalize())
        self.btn_year.setText(str(self.current_date.year))
        
        self.btn_prev.setEnabled(self.current_date.year > 2015)
        
        max_year = date.today().year
        self.btn_next.setEnabled(self.current_date.year < max_year)

        self.clear_grid()

        for col in range(7):
            day_of_week = col + 1 
            day_name = self.q_locale.dayName(day_of_week, QLocale.FormatType.ShortFormat).capitalize()
            lbl_day = QLabel(day_name)
            lbl_day.setFixedSize(self.row_height, self.row_height)
            lbl_day.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(lbl_day, 0, col)

        year = self.current_date.year
        month = self.current_date.month
        
        first_day_of_month = date(year, month, 1)
        start_col = first_day_of_month.weekday() 
        
        if month == 12:
            next_month_boundary = date(year + 1, 1, 1)
        else:
            next_month_boundary = date(year, month + 1, 1)
        days_in_month = (next_month_boundary - first_day_of_month).days

        current_day = 1
        row = 1
        col = start_col

        while current_day <= days_in_month:
            btn_day = QLabel(str(current_day))
            btn_day.setFixedSize(self.row_height, self.row_height)
            self.grid_layout.addWidget(btn_day, row, col)
            current_day += 1
            col += 1
            if col > 6:
                col = 0
                row += 1

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
