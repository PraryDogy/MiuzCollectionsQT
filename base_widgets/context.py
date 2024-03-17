from PyQt5.QtCore import QEvent, QObject, Qt
from PyQt5.QtGui import QFocusEvent
from PyQt5.QtWidgets import QMenu

from styles import Styles


class ContextMenuBase(QMenu):
    def __init__(self, event):
        self.ev = event
        super().__init__()

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setMinimumWidth(200)

        self.setStyleSheet(
            f"""
            QMenu {{
                background-color: {Styles.context_bg_color};
                border: 1px solid {Styles.context_border_color};
                border-radius: {Styles.big_radius};
                padding : 3px;
                color: white;
            }}      
            QMenu::indicator {{
                image: none;
            }}
            QMenu::item {{
                padding: 3 15 3 15;
            }}
            QMenu::item:selected {{
                padding: 3 15 3 15;
                background: {Styles.blue_color};
                border-radius: {Styles.small_radius};
            }}
            QMenu::right-arrow {{
                image: None;
                }}
            """)
    
    def show_menu(self):
        self.exec_(self.ev.globalPos())


class ContextSubMenuBase(QMenu):
    def __init__(self, parent: QMenu, title):
        super().__init__(parent)
        self.setTitle(title)
        self.setMinimumWidth(150)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.mousePressEvent = lambda e: self.raise_()
