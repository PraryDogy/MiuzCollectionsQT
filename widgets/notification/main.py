from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFrame, QGraphicsDropShadowEffect, QLabel, QWidget

from base_widgets import LayoutH
from cfg import cnf
from styles import Names, Themes


class Notification(QFrame):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.setObjectName(Names.notification_widget)
        self.setStyleSheet(Themes.current)

        effect = QGraphicsDropShadowEffect()
        effect.setColor(QColor(0, 0, 0, 240))
        effect.setOffset(0, 0)
        effect.setBlurRadius(15)
        self.setGraphicsEffect(effect)
                
        h_layout = LayoutH(self)
        h_layout.addStretch(1)

        self.label = QLabel(cnf.lng.no_tiff)
        h_layout.addWidget(self.label)

        h_layout.addStretch(1)

        self.hide_timer = QTimer(self)
        self.hide_timer.setInterval(3000)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

        self.hide()

    def show_notify(self, text: str):
        self.label.setText(text)
        self.show()
        self.hide_timer.start()
