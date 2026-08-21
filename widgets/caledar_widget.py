import sys
from datetime import date

from PyQt6.QtCore import QDate, QLocale, Qt, pyqtSignal
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


from PyQt6.QtWidgets import QWidget, QHBoxLayout, QGridLayout, QLabel, QMenu
from PyQt6.QtCore import QDate, QLocale, Qt
from PyQt6.QtGui import QAction

class CustomCalendar(UMainWidget):
    def __init__(self, date_val: QDate = QDate.currentDate()):
        super().__init__()
        self.q_locale = QLocale(QLocale.Language.Russian, QLocale.Country.Russia)
        
        # Полностью переходим на QDate
        self.current_date = date_val
        
        self.row_height = 40
        self.cell_size = (50, 40)
        self.svg_size = (20, 20)
        self.month_btn_width = 75
        self.year_btn_width = 60
        
        self.setWindowTitle("Кастомный Календарь")
        self.set_close_only()
        self.set_always_on_top()
        self.init_ui()
        
        self.central_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Подгоняем размер под контент и жестко фиксируем его
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())

    def init_ui(self):
        # --- Первая строка: Панель навигации (Контейнер) ---
        self.nav_widget = QWidget()
        self.nav_widget.setFixedHeight(self.row_height)
        self.nav_layout = QHBoxLayout(self.nav_widget)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(0)
        
        # Стрелка влево (Предыдущий год)
        self.btn_prev = ClickableSvgWidget("./icons/common/previous.svg")
        self.btn_prev.setFixedSize(*self.svg_size)
        self.btn_prev.clicked.connect(self.prev_year)
        
        # Кнопка выбора месяца с QMenu
        self.btn_month = UPushButton("")
        self.btn_month.setFixedWidth(self.month_btn_width)
        self.menu_month = QMenu(self)
        self.btn_month.setMenu(self.menu_month)
        self.populate_months()

        # Кнопка выбора года с QMenu
        self.btn_year = UPushButton("")
        self.btn_year.setFixedWidth(self.year_btn_width)
        self.menu_year = QMenu(self)
        self.btn_year.setMenu(self.menu_year)
        self.populate_years()
        
        # Стрелка вправо (Следующий год)
        self.btn_next = ClickableSvgWidget("./icons/common/next.svg")
        self.btn_next.setFixedSize(*self.svg_size)
        self.btn_next.clicked.connect(self.next_year)
        
        # Собираем навигационную панель внутри контейнера
        self.nav_layout.addWidget(self.btn_prev)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.btn_month)
        self.nav_layout.addSpacing(5)
        self.nav_layout.addWidget(self.btn_year)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.btn_next)
        
        self.central_layout.addWidget(self.nav_widget)

        # --- Сетка для дней недели и чисел (Контейнер) ---
        self.grid_widget = QWidget()  
        
        # Важно: Фиксируем высоту контейнера сетки на максимум (7 строк по 40px + spacing)
        # Это гарантирует, что adjustSize() сразу выделит место под 6 недель, и ничего не съедет
        max_grid_height = (7 * self.cell_size[1]) + (6 * 5)
        self.grid_widget.setFixedHeight(max_grid_height)
        
        self.grid_layout = QGridLayout(self.grid_widget)  
        self.grid_layout.setSpacing(5)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Прижимаем дни к верху
        
        self.central_layout.addWidget(self.grid_widget)
        
        # Обновляем интерфейс под текущую дату
        self.update_calendar()

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
        max_year = QDate.currentDate().year() # Заменили date.today().year
        for y in range(start_year, max_year + 1):
            action = QAction(str(y), self)
            action.setData(y)
            action.triggered.connect(self.year_selected)
            self.menu_year.addAction(action)

    def month_selected(self):
        action = self.sender()
        if action:
            selected_month = action.data()
            # Пересоздаем QDate с новым месяцем (защита от падения, если текущий день 31, а в новом месяце всего 30 дней)
            target_day = min(self.current_date.day(), QDate(self.current_date.year(), selected_month, 1).daysInMonth())
            self.current_date = QDate(self.current_date.year(), selected_month, target_day)
            self.update_calendar()

    def year_selected(self):
        action = self.sender()
        if action:
            selected_year = action.data()
            # Пересоздаем QDate с новым годом (учитываем високосные года и 29 февраля)
            target_day = min(self.current_date.day(), QDate(selected_year, self.current_date.month(), 1).daysInMonth())
            self.current_date = QDate(selected_year, self.current_date.month(), target_day)
            self.update_calendar()

    def prev_year(self):
        if self.current_date.year() > 2015:
            self.current_date = self.current_date.addYears(-1)
            self.update_calendar()

    def next_year(self):
        max_year = QDate.currentDate().year()
        if self.current_date.year() < max_year:
            self.current_date = self.current_date.addYears(1)
            self.update_calendar()

    def clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def update_calendar(self):
        current_year = self.current_date.year()
        current_month = self.current_date.month()

        current_month_name = self.q_locale.standaloneMonthName(
            current_month,
            QLocale.FormatType.LongFormat
        )
        self.btn_month.setText(current_month_name.capitalize())
        self.btn_year.setText(str(current_year))
        
        self.btn_prev.setEnabled(current_year > 2015)
        
        max_year = QDate.currentDate().year()
        self.btn_next.setEnabled(current_year < max_year)

        self.clear_grid()

        # Отрисовка дней недели
        for col in range(7):
            day_of_week = col + 1 
            day_name = self.q_locale.dayName(day_of_week, QLocale.FormatType.ShortFormat).capitalize()
            lbl_day = QLabel(day_name)
            lbl_day.setFixedSize(*self.cell_size)
            lbl_day.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(lbl_day, 0, col)

        # Отрисовка чисел текущего месяца
        first_day_of_month = QDate(current_year, current_month, 1)
        # В QDate: 1 = Понедельник ... 7 = Воскресенье. Переводим в 0..6
        start_col = first_day_of_month.dayOfWeek() - 1 
        
        days_in_month = self.current_date.daysInMonth()

        current_day = 1
        row = 1
        col = start_col

        while current_day <= days_in_month:
            btn_day = QLabel(str(current_day))
            btn_day.setFixedSize(*self.cell_size)
            btn_day.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
