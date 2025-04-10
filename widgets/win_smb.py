import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLabel, QSpacerItem, QWidget

from base_widgets import LayoutHor, LayoutVer, SvgBtn
from base_widgets.wins import WinSystem
from main_folders import MainFolder
from cfg import Static
from lang import Lang

WARNING_SVG = os.path.join(Static.IMAGES, "warning.svg")

TITLE_NORMAL = f"""
    {Static.TITLE_NORMAL}
    border: 0px;
"""

class WinSmb(WinSystem):
    def __init__(self, text: str = None):
        super().__init__()

        if text:
            self.my_text = text
        else:
            self.my_text = f"{MainFolder.current.name.capitalize()}:\n{Lang.choose_coll_smb}"

        self.setWindowTitle(f"{MainFolder.current.name.capitalize()}: {Lang.no_connection.lower()}")

        self.init_ui()
        self.setFixedSize(330, 80)
        self.setFocus()

    def init_ui(self):
        h_wid = QWidget()
        self.central_layout.addWidget(h_wid)
        h_layout = LayoutHor()
        h_wid.setLayout(h_layout)

        warning = SvgBtn(WARNING_SVG, 40)
        h_layout.addWidget(warning)

        h_layout.addSpacerItem(QSpacerItem(15, 0))

        v_wid = QWidget()
        h_layout.addWidget(v_wid)
        v_lay = LayoutVer()
        v_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        v_wid.setLayout(v_lay)

        descr = QLabel(self.my_text)
        v_lay.addWidget(descr)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.close()