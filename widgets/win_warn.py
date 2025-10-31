from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSizePolicy,
                             QSpacerItem, QVBoxLayout, QWidget)

from cfg import cfg
from system.lang import Lng
from system.shared_utils import SharedUtils

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

        warning = QSvgWidget()
        warning.load(self.svg_warning)
        warning.setFixedSize(self.svg_size, self.svg_size)
        self.content_layout.addWidget(warning)

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

        # self.right_wid.adjustSize()
        # ok_btn.adjustSize()
        # hh = self.right_wid.height() + ok_btn.height() + 15
        # self.resize(self.width(), hh)


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



class WinUpload(WinQuestion):
    def __init__(self, title, path: str):
        super().__init__(title=title, text="Загрузить файлы в:", char_limit=999)
        self.setFixedWidth(400)

        self.text_label.deleteLater()

        container = QWidget()
        self.right_layout.addWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(0, 0, 0, 0)

        current_line = QHBoxLayout()
        main_layout.addLayout(current_line)

        total_width = 0
        max_width = self.width() - 20  # запас для скроллбаров и отступов

        for part in path.split("/"):
            label = QLabel(part)
            label.adjustSize()
            w = label.sizeHint().width()

            if total_width + w > max_width:
                # перенос на новую строку
                current_line = QHBoxLayout()
                main_layout.addLayout(current_line)
                total_width = 0

            current_line.addWidget(label)
            total_width += w + 8  # + отступ

        self.right_layout.addWidget(container)
