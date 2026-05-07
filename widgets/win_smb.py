import os
import sys

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                             QPushButton, QVBoxLayout, QWidget)

from cfg import Cfg
from system.lang import Lng
from system.main_folder import Mf
from widgets._base_widgets import PathWidget, UMainWindow


class WarnWidget(QWidget):
    warn = "images/warning.svg"
    def __init__(self, mf: Mf):
        super().__init__()
        self.setFixedWidth(350)
        h_lay = QHBoxLayout(self)
        h_lay.setContentsMargins(2, 5, 2, 5)
        h_lay.setSpacing(10)

        warn_wid = QSvgWidget()
        warn_wid.load(self.warn)
        warn_wid.setFixedSize(30, 30)
        h_lay.addWidget(warn_wid)

        lines = (
            f"{Lng.access_error_text[Cfg.lng_index]} \"{mf.mf_alias}\".",
            Lng.network_error_text[Cfg.lng_index]
        )
        up_label = QLabel("\n".join(lines))
        up_label.setWordWrap(True)
        h_lay.addWidget(up_label)


class WinSmb(UMainWindow):
    clicked = pyqtSignal(str)

    def __init__(self, mf: Mf):
        super().__init__()
        self.set_close_only()
        self.set_always_on_top()
        self.setWindowTitle(Lng.attention[Cfg.lng_index])
        self.mf = mf
        self.central_layout.setContentsMargins(10, 10, 10, 5)
        self.central_layout.setSpacing(10)

        warn_widget = WarnWidget(mf)
        self.central_layout.addWidget(warn_widget)

        self.path_widget = PathWidget(mf)
        self.central_layout.addWidget(self.path_widget)

        btns_wid = QWidget()
        self.central_layout.addWidget(btns_wid)
        btns_lay = QHBoxLayout(btns_wid)
        btns_lay.setContentsMargins(0, 0, 0, 0)
        btns_lay.setSpacing(10)

        btns_lay.addStretch()
        ok_btn = QPushButton(Lng.ok[Cfg.lng_index])
        ok_btn.clicked.connect(self.ok_clicked)
        ok_btn.setFixedWidth(90)
        btns_lay.addWidget(ok_btn)
        cancel_btn = QPushButton(Lng.cancel[Cfg.lng_index])
        cancel_btn.clicked.connect(self.deleteLater)
        cancel_btn.setFixedWidth(90)
        btns_lay.addWidget(cancel_btn)
        btns_lay.addStretch()

        self.adjustSize()

    def ok_clicked(self):
        if self.path_widget.url:
            self.clicked.emit(self.path_widget.url)
            self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
