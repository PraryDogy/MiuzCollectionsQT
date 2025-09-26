from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QLabel, QPushButton, QSpacerItem, QWidget

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
        self.setFixedWidth(350)

        self.central_layout.setContentsMargins(10, 10, 10, 10)
        self.central_layout.setSpacing(10)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)
        h_layout = UHBoxLayout()
        h_wid.setLayout(h_layout)

        warning = QSvgWidget()
        warning.load(self.svg_warning)
        warning.setFixedSize(self.svg_size, self.svg_size)
        h_layout.addWidget(warning)

        h_layout.addSpacerItem(QSpacerItem(15, 0))

        v_wid = QWidget()
        h_layout.addWidget(v_wid)
        v_lay = UVBoxLayout()
        v_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        v_wid.setLayout(v_lay)

        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        v_lay.addWidget(self.text_label)

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

        self.setMinimumWidth(300)
        self.setMaximumWidth(500)
        self.text_label.setWordWrap(True)
        self.adjustSize()


class WinQuestion(BaseWinWarn):
    ok_clicked = pyqtSignal()

    def __init__(self, title: str, text: str):
        super().__init__(title, text)

        btn_wid = QWidget()
        btn_lay = UHBoxLayout()
        btn_lay.setSpacing(10)
        btn_lay.setContentsMargins(0, 10, 0, 0)
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
        self.adjustSize()


class WinSmb(WinWarn):
    def __init__(self):
        super().__init__(
            Lng.attention[Cfg.lng],
            "\n" + Lng.folder_access_error[Cfg.lng] + "\n"
        )
                