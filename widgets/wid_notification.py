from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QLabel, QWidget

from styles import Names, Themes
from signals import SignalsApp

class Notification(QLabel):
    def __init__(self, parent: QWidget):
        super().__init__(parent=parent, text="Notification")
        self.my_parent = parent
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setObjectName(Names.notification_widget)
        self.setStyleSheet(Themes.current)

    def show_notify(self, text: str):
        self.setText(text)
        self.show()
        QTimer.singleShot(3000, self.hide)