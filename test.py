import sys
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# Ваш собственный кастомный календарь
class CustomCalendarWidget(QWidget):

  def __init__(self, parent=None):
    super().__init__(parent)

    # 1. МАГИЯ ПОПАПА: Делаем виджет всплывающим и автозакрывающимся
    self.setWindowFlags(Qt.WindowType.Popup)

    # Пример вашей кастомной структуры
    layout = QVBoxLayout(self)
    layout.setContentsMargins(10, 10, 10, 10)

    # Шапка (например, месяц и год)
    lbl_title = QLabel("<b>Сентябрь 2026</b>")
    layout.addWidget(lbl_title)

    # Ваша кастомная сетка дней
    grid_layout = QGridLayout()
    for row in range(3):
      for col in range(3):
        day_btn = QPushButton(str(row * 3 + col + 1))
        # При клике на день можно закрывать попап
        day_btn.clicked.connect(self.hide)
        grid_layout.addWidget(day_btn, row, col)

    layout.addLayout(grid_layout)


# Главное окно
class MainWindow(QWidget):

  def __init__(self):
    super().__init__()
    self.setWindowTitle("Главное окно")
    self.resize(400, 300)

    layout = QVBoxLayout(self)

    # Кнопка вызова календаря
    self.btn_open = QPushButton("Открыть мой календарь")
    self.btn_open.setFixedWidth(200)
    layout.addWidget(self.btn_open)

    # Создаем экземпляр вашего кастомного календаря
    self.calendar_popup = CustomCalendarWidget(self)

    # Привязываем клик
    self.btn_open.clicked.connect(self.toggle_calendar)

  def toggle_calendar(self):
    # Вычисляем позицию прямо под кнопкой
    global_pos = self.btn_open.mapToGlobal(QPoint(0, self.btn_open.height()))
    self.calendar_popup.move(global_pos)
    self.calendar_popup.show()


if __name__ == "__main__":
  app = QApplication(sys.argv)
  window = MainWindow()
  window.show()
  sys.exit(app.exec())