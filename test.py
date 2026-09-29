import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget


class NumberLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        self.bg_pixmap = QPixmap("icons/common/calendar.svg")
        self.active = False

        self.setFixedSize(40, 40)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_active(self, active: bool):
        self.active = active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        if self.active:
            painter.drawPixmap(self.rect(), self.bg_pixmap)

        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            self.text()
        )


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Number Label")
        self.setFixedSize(300, 200)

        self.number = NumberLabel("1")

        self.button = QPushButton("Переключить")
        self.button.clicked.connect(self.toggle)

        layout = QVBoxLayout(self)
        layout.addWidget(self.number, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.button)

    def toggle(self):
        self.number.set_active(not self.number.active)


app = QApplication(sys.argv)

window = Window()
window.show()

sys.exit(app.exec())