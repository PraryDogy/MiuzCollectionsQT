from PyQt5.QtWidgets import QProgressBar, QWidget

from styles import Names, Themes


class CustomProgressBar(QProgressBar):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)

        self.setFixedHeight(7)
        self.setObjectName(Names.progress)
        self.setStyleSheet(Themes.current)