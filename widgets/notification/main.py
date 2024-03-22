from PyQt5.QtCore import QRect, Qt, QTimer
from PyQt5.QtWidgets import (QApplication, QFrame, QGraphicsDropShadowEffect,
                             QLabel, QWidget)

from base_widgets import LayoutH
from cfg import cnf
from signals import gui_signals_app
from styles import Styles


class Notification(QFrame):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setStyleSheet(
            f"""
            background-color: {Styles.blue_color};
            border-radius: {Styles.big_radius};
            """)

        effect = QGraphicsDropShadowEffect()
        effect.setOffset(0, 0)
        effect.setBlurRadius(28)
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
