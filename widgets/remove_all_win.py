import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
                             QWidget)

from base_widgets.svg_btn import SvgBtn
from base_widgets.wins import WinSystem
from cfg import Static
from lang import Lang
from main_folder import MainFolder


class RemoveAllWin(WinSystem):
    warning_svg = os.path.join(Static.images_dir, "warning.svg")
    ok_pressed = pyqtSignal()
    cancel_pressed = pyqtSignal()
    svg_size = 50

    def __init__(self, main_folder: MainFolder):
        """
        Сигналы: ok_pressed, cancel_pressed
        """
        super().__init__()
        self.setWindowTitle(Lang.attention)
        self.central_layout.setSpacing(5)

        first_row_wid = QWidget()
        self.central_layout.addWidget(first_row_wid)
        first_row_lay = QHBoxLayout()
        first_row_lay.setContentsMargins(0, 0, 0, 0)
        first_row_wid.setLayout(first_row_lay)

        warn = SvgBtn(self.warning_svg, self.svg_size)
        first_row_lay.addWidget(warn)

        title = f"{Lang.collections}: {main_folder.name}\n"
        descr = Lang.remove_all_descr    
        t = title + descr
        lbl = QLabel(t)
        first_row_lay.addWidget(lbl)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)
        h_lay = QHBoxLayout()
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)
        h_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_wid.setLayout(h_lay)

        ok_btn = QPushButton(Lang.ok)
        ok_btn.clicked.connect(self.ok_cmd)
        ok_btn.setFixedWidth(90)
        h_lay.addWidget(ok_btn)

        can_btn = QPushButton(Lang.cancel)
        can_btn.clicked.connect(self.cancel_cmd)
        can_btn.setFixedWidth(90)
        h_lay.addWidget(can_btn)

        self.adjustSize()

    def ok_cmd(self):
        self.ok_pressed.emit()
        self.deleteLater()

    def cancel_cmd(self):
        self.cancel_pressed.emit()
        self.deleteLater()

    def closeEvent(self, a0):
        a0.ignore()
