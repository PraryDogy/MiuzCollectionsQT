from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QLabel, QPushButton, QSizePolicy, QSpacerItem,
                             QWidget)

from cfg import Cfg
from system.lang import Lng
from system.main_folder import Mf

from ._base_widgets import SingleActionWindow, UHBoxLayout, UVBoxLayout


class BaseWinWarn(SingleActionWindow):
    svg_warning = "./images/warning.svg"
    svg_size = 40

    def __init__(self, title: str, text: str):
        super().__init__()
        self.setWindowTitle(title)
        self.setMinimumWidth(290)
        self.setMaximumWidth(370)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)
        self.content_layout = UHBoxLayout()
        h_wid.setLayout(self.content_layout)

        warning = QSvgWidget()
        warning.load(self.svg_warning)
        warning.setFixedSize(self.svg_size, self.svg_size)
        self.content_layout.addWidget(warning)

        self.content_layout.addSpacerItem(QSpacerItem(15, 0))

        self.right_wid = QWidget()
        self.content_layout.addWidget(self.right_wid)
        self.right_layout = UVBoxLayout()
        self.right_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.right_wid.setLayout(self.right_layout)

        text = self.insert_linebreaks(text)
        self.text_label = QLabel(text)
        self.right_layout.addWidget(self.text_label)

        self.adjustSize()

    def insert_linebreaks(self, text: str, n: int = 35) -> str:
        return '\n'.join(
            text[i:i+n]
            for i in range(0, len(text), n)
        )

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.deleteLater()


class WinWarn(BaseWinWarn):
    def __init__(self, title: str, text: str):
        super().__init__(title, text)
        ok_btn = QPushButton(text=Lng.ok[Cfg.lng])
        ok_btn.setFixedWidth(90)
        ok_btn.clicked.connect(self.deleteLater)
        self.central_layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class WinQuestion(BaseWinWarn):
    ok_clicked = pyqtSignal()

    def __init__(self, title: str, text: str):
        super().__init__(title, text)

        btn_wid = QWidget()
        btn_lay = UHBoxLayout()
        btn_lay.setSpacing(10)
        btn_wid.setLayout(btn_lay)

        ok_btn = QPushButton(Lng.ok[Cfg.lng])
        ok_btn.clicked.connect(self.ok_clicked.emit)
        ok_btn.setFixedWidth(90)

        cancel_btn = QPushButton(Lng.cancel[Cfg.lng])
        cancel_btn.setFixedWidth(90)
        cancel_btn.clicked.connect(self.deleteLater)

        btn_lay.addStretch()
        btn_lay.addWidget(ok_btn)
        btn_lay.addWidget(cancel_btn)
        btn_lay.addStretch()

        self.central_layout.addWidget(btn_wid)
