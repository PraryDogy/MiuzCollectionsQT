from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel

from utils.utils import Utils


class Btn(QLabel):
    def __init__(self, text: str):
        super().__init__(text=text)
        self.setFixedSize(80, 28)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setObjectName("base_btn")
        Utils.style(wid=self)
