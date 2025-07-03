import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QSpacerItem,
                             QWidget)

from cfg import JsonData, Static
from system.lang import Lang
from system.main_folder import MainFolder
from system.utils import MainUtils

from ._base_widgets import (SvgBtn, UHBoxLayout, UTextEdit, UVBoxLayout,
                            WinSystem)

WARNING_SVG = os.path.join(Static.INNER_IMAGES, "warning.svg")


class WinWarn(WinSystem):
    def __init__(self, title: str, text: str):
        super().__init__()
        self.setWindowTitle(title)
        self.my_text = text

        self.central_layout.setContentsMargins(10, 10, 10, 10)
        self.central_layout.setSpacing(10)
        self.init_ui()
        self.adjustSize()

    def init_ui(self):
        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)
        h_layout = UHBoxLayout()
        h_wid.setLayout(h_layout)

        warning = SvgBtn(WARNING_SVG, 40)
        h_layout.addWidget(warning)

        h_layout.addSpacerItem(QSpacerItem(15, 0))

        v_wid = QWidget()
        h_layout.addWidget(v_wid)
        v_lay = UVBoxLayout()
        v_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        v_wid.setLayout(v_lay)

        descr = QLabel(self.my_text)
        v_lay.addWidget(descr)

        ok_btn = QPushButton(text=Lang.ok)
        ok_btn.setFixedWidth(90)
        ok_btn.clicked.connect(self.close)
        self.central_layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.deleteLater()


class WinError(WinSystem):
    def __init__(self, title: str, text: str):
        super().__init__()
        self.setWindowTitle(title)
        self.setFixedSize(350, 350)
        self.my_text = text

        self.central_layout.setContentsMargins(10, 10, 10, 10)
        self.central_layout.setSpacing(10)
        self.init_ui()

    def init_ui(self):
        text_edit = UTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(self.my_text)
        self.central_layout.addWidget(text_edit)

        # Отступ между текстом и кнопкой
        self.central_layout.addSpacerItem(QSpacerItem(0, 15))

        # Кнопка OK
        ok_btn = QPushButton(text=Lang.ok)
        ok_btn.setFixedWidth(90)
        ok_btn.clicked.connect(self.close)
        self.central_layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.deleteLater()