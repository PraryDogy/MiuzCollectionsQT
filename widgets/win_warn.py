import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout, QLabel

from cfg import JsonData, Static
from system.lang import Lng

from ._base_widgets import SelectableLabel, UMainWidget, UPushButton


class NewSelectableLabel(SelectableLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.setWordWrap(True)
        self.adjustSize()


class ConfirmWindow(UMainWidget):
    ok_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()
    ww = 360
    icon_path = os.path.join(Static.internal_icons, "warning.svg")

    def __init__(self, text: str):
        super().__init__()
        self.set_always_on_top()
        self.set_close_only()
        self.setWindowTitle(Lng.attention[JsonData.lng_index])
        self.setMaximumWidth(360)
        self.setMinimumWidth(280)

        text_layout = QHBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(15)
        self.central_layout.addLayout(text_layout)

        self.svg_widget = QSvgWidget()
        self.svg_widget.load(self.icon_path)
        self.svg_widget.setFixedSize(50, 50)
        text_layout.addWidget(self.svg_widget)

        self.text_wid = NewSelectableLabel(text)
        text_layout.addWidget(self.text_wid)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.central_layout.addLayout(btn_layout)

        self.ok_btn = UPushButton(Lng.ok[JsonData.lng_index])
        self.ok_btn.clicked.connect(self.ok_clicked.emit)
        btn_layout.addWidget(self.ok_btn)

        self.cancel_btn = UPushButton(Lng.cancel[JsonData.lng_index])
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
        self.cancel_btn.clicked.connect(self.deleteLater)
        btn_layout.addWidget(self.cancel_btn)

        self.central_layout.setContentsMargins(10, 10, 10, 2)
        self.central_layout.setSpacing(10)

        self.adjustSize()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_clicked.emit()
        return super().keyPressEvent(a0)
    

class WarningWindow(ConfirmWindow):
    def __init__(self, text):
        super().__init__(text)
        self.cancel_btn.hide()
        self.ok_btn.disconnect()
        self.ok_btn.clicked.connect(self.deleteLater)
        self.adjustSize()

    def keyPressEvent(self, a0: QKeyEvent):
        if a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.deleteLater()
        return super().keyPressEvent(a0)