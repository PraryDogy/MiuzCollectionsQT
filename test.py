from PyQt5.QtWidgets import QApplication, QCalendarWidget, QWidget, QVBoxLayout
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QTextCharFormat, QBrush, QColor
import sys

class RangeCalendar(QWidget):
    def __init__(self):
        super().__init__()
        self.start_date = None
        self.end_date = None

        layout = QVBoxLayout(self)
        self.calendar = QCalendarWidget()
        layout.addWidget(self.calendar)

        self.calendar.clicked.connect(self.on_date_clicked)

        # формат для подсветки
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QBrush(QColor(100, 150, 255, 100)))

        # формат для сброса
        self.reset_format = QTextCharFormat()

    def on_date_clicked(self, date: QDate):
        if self.start_date is None:
            self.start_date = date
            self.end_date = None
        elif self.end_date is None:
            if date < self.start_date:
                self.end_date = self.start_date
                self.start_date = date
            else:
                self.end_date = date
        else:
            # начинаем новый выбор диапазона
            self.clear_range()
            self.start_date = date
            self.end_date = None

        self.highlight_range()

    def clear_range(self):
        if self.start_date and self.end_date:
            d = QDate(self.start_date)
            while d <= self.end_date:
                self.calendar.setDateTextFormat(d, self.reset_format)
                d = d.addDays(1)
        elif self.start_date:
            self.calendar.setDateTextFormat(self.start_date, self.reset_format)

    def highlight_range(self):
        self.clear_range()
        if self.start_date and self.end_date:
            d = QDate(self.start_date)
            while d <= self.end_date:
                self.calendar.setDateTextFormat(d, self.highlight_format)
                d = d.addDays(1)
        elif self.start_date:
            self.calendar.setDateTextFormat(self.start_date, self.highlight_format)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = RangeCalendar()
    w.show()
    sys.exit(app.exec_())