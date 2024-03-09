from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QPushButton, QScrollArea

from signals import gui_signals_app

from styles import Styles


class UpBtn(QPushButton):
    def __init__(self, parent: QScrollArea):
        super(UpBtn, self).__init__(text="▲", parent=parent)
        self.side = 40
    
        self.setFixedSize(self.side, self.side)
        self.setStyleSheet(
            f"""
            background-color: {Styles.thumbs_up_color};
            border-radius: {int(self.side/2)}px;
            color: white;
            """)
        
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(3)  # Радиус размытия тени
        shadow_effect.setColor(QColor(0, 0, 0))  # Цвет тени
        shadow_effect.setOffset(0, 0)  # Смещение тени
        self.setGraphicsEffect(shadow_effect)

    def mouseReleaseEvent(self, event):
        gui_signals_app.scroll_top.emit()