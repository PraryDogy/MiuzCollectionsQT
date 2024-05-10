from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel

from styles import Styles


class Btn(QLabel):
    def __init__(self, text):
        super().__init__(text=text)
        self.setFixedSize(80, 28)
        self.setAlignment(Qt.AlignCenter)

        self.setStyleSheet(
            f"""
            background-color: {Styles.thumbs_item_color};
            border-radius: {Styles.small_radius};
            """)
