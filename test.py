import sys
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint

class HoverLabel(QLabel):
    def __init__(self, text):
        super().__init__()
        self.setText(text)
        self.setAlignment(Qt.AlignCenter)
        self.setMouseTracking(True)  # Включаем отслеживание движения мыши

        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(5000)  # Длительность анимации в миллисекундах

    def enterEvent(self, event):
        super().enterEvent(event)
        # Начинаем анимацию при наведении мыши
        start_pos = self.pos()
        end_pos = self.pos() + QPoint(self.width(), 0)  # Смещаем текст на ширину виджета
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        self.animation.start()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        # Останавливаем анимацию при уходе мыши
        self.animation.stop()
        self.move(0, self.pos().y())  # Возвращаем текст на исходное место

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        label = HoverLabel("Hover me to see running text!")
        layout.addWidget(label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(300, 200)
    window.show()
    sys.exit(app.exec_())
