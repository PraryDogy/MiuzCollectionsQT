from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QLabel, QWidget

from styles import Names, Themes


class Notification(QLabel):
    def __init__(self, parent: QWidget):
        super().__init__(parent=parent, text="Notification")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setObjectName(Names.notification_widget)
        self.setStyleSheet(Themes.current)

    def show_notify(self, text: str):
        self.setText(text)
        self.show()
        QTimer.singleShot(3000, self.hide)