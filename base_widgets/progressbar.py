from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QProgressBar, QWidget

from styles import Names, Themes


class CustomProgressBar(QProgressBar):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setTextVisible(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(7)