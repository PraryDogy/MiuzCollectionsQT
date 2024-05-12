from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel

from styles import Names, default_theme


class Btn(QLabel):
    def __init__(self, text):
        super().__init__(text=text)
        self.setFixedSize(80, 28)
        self.setAlignment(Qt.AlignCenter)

        self.setObjectName(Names.base_btn)
        self.setStyleSheet(default_theme)

