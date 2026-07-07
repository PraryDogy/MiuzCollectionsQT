from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

app = QApplication([])

# Проверяем, что используется родной стиль macOS
app.setStyle('Macintosh') 

# Создаем и настраиваем палитру
palette = QPalette()
# Меняем цвет фона окон на темно-серый
palette.setColor(QPalette.Window, QColor("#f84949"))
# Меняем цвет текста на белый
palette.setColor(QPalette.WindowText, Qt.white)
# Меняем цвет кнопок (в macOS повлияет на фокус и границы)
palette.setColor(QPalette.Button, QColor("#CCF320")) 
palette.setColor(QPalette.ButtonText, Qt.white)

# Применяем палитру ко всему приложению
app.setPalette(palette)

# Пример интерфейса
window = QWidget()
layout = QVBoxLayout()
btn = QPushButton("Системная кнопка")
layout.addWidget(btn)
window.setLayout(layout)
window.show()

app.exec_()
