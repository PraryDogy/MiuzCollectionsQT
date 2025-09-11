from PyQt5.QtWidgets import QMainWindow, QLabel, QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
import sys

class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()

        # Центральный виджет и layout
        central = QWidget()
        self.setCentralWidget(central)
        self.layout = QVBoxLayout(central)
        self.layout.addStretch()  # чтобы QLabel был снизу

        # Статусная метка слева-снизу
        self.status_label = QLabel("Статус")
        self.status_label.setAlignment(Qt.AlignLeft)  # левое выравнивание
        self.layout.addWidget(self.status_label, alignment=Qt.AlignLeft)

        self.show()

        # Список текстов для эмуляции изменения
        self.texts = [f"Статус {i}" for i in range(0, 10000000000, 1000)]
        self.index = 0

        # Таймер для обновления текста каждые 10 мс
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_text)
        self.timer.start(10)  # 10 мс ≈ 0.01 с

    def update_text(self):
        if self.index >= len(self.texts):
            self.timer.stop()
            return
        self.status_label.setText(self.texts[self.index])
        self.index += 1

app = QApplication(sys.argv)
win = MainWin()
sys.exit(app.exec_())
