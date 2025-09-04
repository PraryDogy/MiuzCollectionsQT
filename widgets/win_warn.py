import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QApplication, QLabel, QPushButton, QSpacerItem,
                             QWidget)

from cfg import JsonData, Static
from system.lang import Lng
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

        ok_btn = QPushButton(text=Lng.ok[JsonData.lng])
        ok_btn.setFixedWidth(90)
        ok_btn.clicked.connect(self.close)
        self.central_layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.deleteLater()


class WinSmb(WinWarn):
    def __init__(self):
        super().__init__(
            Lng.no_connection[JsonData.lng],
            Lng.no_connection_descr[JsonData.lng]
        )


class WinQuestion(WinSystem):
    ok_clicked = pyqtSignal()
    lang = (
        ("Ок", "Ok"),
        ("Отмена", "Cancel"),
    )

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

        # кнопки
        btn_wid = QWidget()
        btn_lay = UHBoxLayout()
        btn_lay.setSpacing(10)
        btn_lay.setContentsMargins(0, 10, 0, 0)
        btn_wid.setLayout(btn_lay)

        ok_btn = QPushButton(Lng.ok[JsonData.lng])
        ok_btn.clicked.connect(self.ok_clicked.emit)
        ok_btn.setFixedWidth(90)
        ok_btn.clicked.connect(self.close)

        cancel_btn = QPushButton(Lng.cancel[JsonData.lng])
        cancel_btn.setFixedWidth(90)
        cancel_btn.clicked.connect(self.deleteLater)

        btn_lay.addStretch()
        btn_lay.addWidget(ok_btn)
        btn_lay.addWidget(cancel_btn)
        btn_lay.addStretch()

        self.central_layout.addWidget(btn_wid)


    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.deleteLater()