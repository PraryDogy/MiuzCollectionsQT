import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QComboBox, QDateEdit, 
                             QLabel, QDialog)
from PyQt6.QtCore import QDate, Qt


class DateFilterDialog(QDialog):
    """Отдельное компактное окно для фильтрации дат (Tool Window)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        # Настройка стиля окна: компактное окно-инструмент, всегда поверх главного
        self.setWindowTitle("Фильтр по датам")
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowCloseButtonHint)
        self.setModal(False) # Оставляем галерею кликабельной во время выбора дат
        
        # Основной вертикальный лейаут
        layout = QVBoxLayout(self)
        
        # 1. Блок быстрых пресетов
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Период:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Все время", "Сегодня", "За неделю", "За месяц", "За год", "Указать диапазон..."
        ])
        self.preset_combo.currentIndexChanged.connect(self.handle_preset_change)
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)
        
        # 2. Блок ручного выбора дат (Диапазон)
        date_layout = QHBoxLayout()
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_to = QDateEdit(QDate.currentDate())
        
        for widget in [self.date_from, self.date_to]:
            widget.setCalendarPopup(True) # Встроенный выпадающий календарь
            widget.setEnabled(False)      # По умолчанию заблокирован
            
        date_layout.addWidget(QLabel("С:"))
        date_layout.addWidget(self.date_from)
        date_layout.addWidget(QLabel("По:"))
        date_layout.addWidget(self.date_to)
        layout.addLayout(date_layout)
        
        # 3. Кнопка применить
        self.apply_btn = QPushButton("Применить фильтр")
        self.apply_btn.clicked.connect(self.apply_filter)
        layout.addWidget(self.apply_btn)
        
    def handle_preset_change(self, index):
        is_custom = (self.preset_combo.currentText() == "Указать диапазон...")
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
        start_date = self.date_from.date().toPyDate()
        end_date = self.date_to.date().toPyDate()
        preset_text = self.preset_combo.currentText()
        
        # Получаем доступ к главному окну и передаем ему даты
        if self.parent():
            self.parent().on_date_filter_applied(preset_text, start_date, end_date)
        
        self.close() # Закрываем окошко после применения фильтра


class MainWindow(QMainWindow):
    """Пример вашего главного окна галереи"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Моя Фото Галерея")
        self.resize(800, 600)
        
        # Инициализируем окно фильтра, передавая self как родителя
        self.filter_dialog = DateFilterDialog(self)
        
        # Интерфейс главного окна
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        self.open_filter_btn = QPushButton("📅 Поиск по датам")
        self.open_filter_btn.clicked.connect(self.show_filter_dialog)
        layout.addWidget(self.open_filter_btn)
        
        # Сюда встанет ваша сетка изображений (QGridLayout)
        self.gallery_placeholder = QLabel("Здесь находится ваша сетка с фото...", self)
        self.gallery_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.gallery_placeholder)
        
        self.setCentralWidget(central_widget)
        
    def show_filter_dialog(self):
        # Магия позиционирования: открываем окно фильтра прямо под кнопкой вызова
        btn_pos = self.open_filter_btn.mapToGlobal(self.open_filter_btn.rect().bottomLeft())
        self.filter_dialog.move(btn_pos)
        self.filter_dialog.show()
        self.filter_dialog.raise_()
        self.filter_dialog.activateWindow()
        
    def on_date_filter_applied(self, preset, start_date, end_date):
        """Этот метод ловит данные из окна фильтра"""
        log_text = f"Фильтр: {preset} | Диапазон: с {start_date} по {end_date}"
        self.gallery_placeholder.setText(f"Сетка обновлена!\n{log_text}")
        print(log_text)
        # TODO: Добавьте сюда вашу логику фильтрации элементов QGridLayout


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
