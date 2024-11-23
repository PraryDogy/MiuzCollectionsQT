from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QPushButton

from utils.utils import Utils


class Btn(QLabel):
    def __init__(self, text: str):
        super().__init__(text=text)
        self.setFixedSize(80, 28)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class Btn(QPushButton):
    def __init__(self, text: str):
        super().__init__(text=text)
        self.setFixedWidth(80)
        # self.setAlignment(Qt.AlignmentFlag.AlignCenter)