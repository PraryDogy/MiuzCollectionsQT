from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QColorDialog, QVBoxLayout, QLabel
from PyQt5.QtGui import QColor
import sys
import numpy as np
import colorsys
import cv2

class ColorWheelDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Цветовое колесо")
        self.resize(200, 200)

        layout = QVBoxLayout(self)

        self.label = QLabel("Синий диапазон", self)
        layout.addWidget(self.label)

        # пример диапазона HSV
        lower_hsv = np.array([100, 80, 80])
        upper_hsv = np.array([140, 255, 255])

        # конвертируем HSV -> RGB (0-255)
        lower_rgb = tuple(int(c*255/255) for c in cv2.cvtColor(np.uint8([[lower_hsv]]), cv2.COLOR_HSV2RGB)[0][0])
        upper_rgb = tuple(int(c*255/255) for c in cv2.cvtColor(np.uint8([[upper_hsv]]), cv2.COLOR_HSV2RGB)[0][0])

        # отображаем как цвет кнопки
        self.btn = QPushButton("Показать цвет", self)
        self.btn.setStyleSheet(f"background-color: rgb{lower_rgb};")
        self.btn.clicked.connect(self.show_color_dialog)
        layout.addWidget(self.btn)

    def show_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            print("Выбран цвет:", color.name())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ColorWheelDemo()
    w.show()
    sys.exit(app.exec_())
