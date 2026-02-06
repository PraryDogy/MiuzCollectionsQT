import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                             QSpacerItem, QVBoxLayout, QWidget)

from cfg import cfg
from system.lang import Lng

from ._base_widgets import SingleActionWindow, UHBoxLayout, UVBoxLayout
from .path_widget import PathWidget

class BaseWinWarn(SingleActionWindow):
    svg_warning = "./images/warning.svg"
    svg_size = 40

    def __init__(self, title: str, text: str, char_limit: int):
        super().__init__()
        self.setWindowTitle(title)
        self.setMinimumSize(200, 1)
        self.resize(200, 1)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)
        self.content_layout = UHBoxLayout()
        h_wid.setLayout(self.content_layout)

        self.svg_wid = QSvgWidget()
        self.svg_wid.load(self.svg_warning)
        self.svg_wid.setFixedSize(self.svg_size, self.svg_size)
        self.content_layout.addWidget(self.svg_wid)

        self.content_layout.setSpacing(15)

        self.right_wid = QWidget()
        self.content_layout.addWidget(self.right_wid)
        self.right_layout = UVBoxLayout()
        self.right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.right_wid.setLayout(self.right_layout)

        # text = SharedUtils.insert_linebreaks(text, char_limit)
        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        self.right_layout.addWidget(self.text_label)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.deleteLater()


class WinWarn(BaseWinWarn):
    def __init__(self, title: str, text: str, char_limit: int = 40):
        super().__init__(title, text, char_limit)
        
        ok_btn = QPushButton(text=Lng.ok[cfg.lng])
        ok_btn.setFixedWidth(90)
        ok_btn.clicked.connect(self.deleteLater)
        self.central_layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.central_layout.setContentsMargins(5, 5, 5, 10)


class WinQuestion(BaseWinWarn):
    ok_clicked = pyqtSignal()

    def __init__(self, title: str, text: str, char_limit = 40):
        super().__init__(title, text, char_limit)

        btn_wid = QWidget()
        btn_lay = UHBoxLayout()
        btn_lay.setSpacing(10)
        btn_wid.setLayout(btn_lay)

        ok_btn = QPushButton(Lng.ok[cfg.lng])
        ok_btn.clicked.connect(self.ok_clicked.emit)
        ok_btn.setFixedWidth(90)

        cancel_btn = QPushButton(Lng.cancel[cfg.lng])
        cancel_btn.setFixedWidth(90)
        cancel_btn.clicked.connect(self.deleteLater)

        btn_lay.addStretch()
        btn_lay.addWidget(ok_btn)
        btn_lay.addWidget(cancel_btn)
        btn_lay.addStretch()

        self.central_layout.addWidget(btn_wid)

    def keyPressEvent(self, a0):
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.ok_clicked.emit()
        return super().keyPressEvent(a0)


class WinUpload(WinQuestion):
    arrow = "▸"
    ww = 380

    def __init__(self, path: str):
        super().__init__(title=Lng.upload_in[cfg.lng], text=None, char_limit=0)
        self.central_layout.setContentsMargins(10, 5, 10, 0)
        self.setFixedWidth(self.ww)
        self.text_label.deleteLater()

        self.text_label = PathWidget(path)
        self.right_layout.addWidget(self.text_label)
        self.adjustSize()
        self.setFixedHeight(self.height() - 20) # срезаем лишнюю высоту
