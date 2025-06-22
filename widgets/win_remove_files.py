import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
                             QWidget)

from base_widgets.svg_btn import SvgBtn
from base_widgets.wins import WinSystem
from cfg import Static
from lang import Lang
from utils.tasks import RemoveFilesTask
from utils.main import UThreadPool


class RemoveFilesWin(WinSystem):
    warning_svg = os.path.join(Static.images_dir, "warning.svg")
    finished_ = pyqtSignal()
    svg_size = 50

    def __init__(self, img_path_list: list[str]):
        super().__init__()
        self.setWindowTitle(Lang.attention)
        self.img_path_list = img_path_list

        first_row_wid = QWidget()
        self.central_layout.addWidget(first_row_wid)
        first_row_lay = QHBoxLayout()
        first_row_lay.setContentsMargins(0, 0, 0, 0)
        first_row_wid.setLayout(first_row_lay)

        warn = SvgBtn(self.warning_svg, RemoveFilesWin.svg_size)
        first_row_lay.addWidget(warn)

        t = f"{Lang.move_to_trash} ({len(self.img_path_list)})?"
        question = QLabel(text=t)
        first_row_lay.addWidget(question)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)
        h_lay = QHBoxLayout()
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(10)
        h_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_wid.setLayout(h_lay)

        ok_btn = QPushButton(Lang.ok)
        ok_btn.clicked.connect(self.cmd_)
        ok_btn.setFixedWidth(90)
        h_lay.addWidget(ok_btn)

        can_btn = QPushButton(Lang.cancel)
        can_btn.clicked.connect(self.deleteLater)
        can_btn.setFixedWidth(90)
        h_lay.addWidget(can_btn)

        self.adjustSize()

    def cmd_(self, *args):
        self.finished_.emit()
        self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()

        elif a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.cmd_()
        return super().keyPressEvent(a0)
    