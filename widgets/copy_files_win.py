from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QLabel, QProgressBar, QWidget

from ._base_widgets import UHBoxLayout, UVBoxLayout, WinSystem


class ProgressbarWin(WinSystem):
    cancel = pyqtSignal()

    def __init__(self, title: str):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setWindowTitle(title)
        self.setFixedSize(350, 60)

        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)
        h_lay = UHBoxLayout()
        h_lay.setSpacing(10)
        h_wid.setLayout(h_lay)

        left_side_icon = QSvgWidget("./images/files.svg")
        left_side_icon.setFixedSize(40, 40)
        h_lay.addWidget(left_side_icon)

        right_side_wid = QWidget()
        right_side_lay = UVBoxLayout()
        right_side_wid.setLayout(right_side_lay)
        h_lay.addWidget(right_side_wid)

        self.above_label = QLabel()
        right_side_lay.addWidget(self.above_label)

        progressbar_row = QWidget()
        right_side_lay.addWidget(progressbar_row)
        progressbar_lay = UHBoxLayout()
        progressbar_lay.setSpacing(10)
        progressbar_row.setLayout(progressbar_lay)

        self.progressbar = QProgressBar()
        self.progressbar.setTextVisible(False)
        self.progressbar.setFixedHeight(6)
        self.progressbar.setFixedWidth(250)
        progressbar_lay.addWidget(self.progressbar)

        self.cancel_btn = QSvgWidget("./images/clear.svg")
        self.cancel_btn.setFixedSize(15, 15)
        self.cancel_btn.mouseReleaseEvent = self.cancel_cmd
        progressbar_lay.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.below_label = QLabel()
        right_side_lay.addWidget(self.below_label)

    def cancel_cmd(self, *args):
        self.cancel.emit()
        self.deleteLater()
