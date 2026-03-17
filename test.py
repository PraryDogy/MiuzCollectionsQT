import sys
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                             QLabel, QDateEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import QDate, Qt

class DateApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Работа с QDateEdit")
        self.setFixedSize(300, 250)
        
        layout = QVBoxLayout()

        # 1. Поле для начальной даты
        layout.addWidget(QLabel("Дата начала:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)  # Включаем выпадающий календарь
        self.start_date_edit.setDate(QDate.currentDate()) # Устанавливаем сегодня
        layout.addWidget(self.start_date_edit)

        # 2. Поле для конечной даты
        layout.addWidget(QLabel("Дата конца:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate().addDays(7)) # + неделя
        layout.addWidget(self.end_date_edit)

        # 3. Кнопка действия
        self.btn = QPushButton("Рассчитать разницу")
        self.btn.clicked.connect(self.calculate_diff)
        layout.addWidget(self.btn)

        # 4. Метка для результата
        self.result_label = QLabel("Выберите даты")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    def calculate_diff(self):
        # Получаем объекты QDate
        start = self.start_date_edit.date()
        end = self.end_date_edit.date()

        # Считаем разницу в днях
        days = start.daysTo(end)

        if days < 0:
            self.result_label.setText("Ошибка: Конец раньше начала!")
            self.result_label.setStyleSheet("color: red;")
        else:
            self.result_label.setText(f"Разница: {days} дней")
            self.result_label.setStyleSheet("color: green; font-weight: bold;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DateApp()
    window.show()
    sys.exit(app.exec())
