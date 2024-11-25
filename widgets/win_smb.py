import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLabel, QSpacerItem, QWidget

from base_widgets import LayoutHor, LayoutVer, SvgBtn
from base_widgets.wins import WinSystem
from cfg import BRANDS, TITLE_NORMAL, JsonData
from lang import Lang

IMAGES = "images"
WARNING_SVG = os.path.join(IMAGES, "warning.svg")

TITLE_NORMAL = f"""
    {TITLE_NORMAL}
    border: 0px;
"""

class WinSmb(WinSystem):
    def __init__(self, text: str = None):
        super().__init__()

        if text:
            self.my_text = text
        else:
            self.my_text = Lang.choose_coll_smb

        self.setWindowTitle(Lang.no_connection)

        self.init_ui()
        self.setFixedSize(330, 100)
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

        brand: str = BRANDS[JsonData.brand_ind]
        title = QLabel(text=brand.capitalize())
        title.setStyleSheet(TITLE_NORMAL)
        v_lay.addWidget(title)

        descr = QLabel(self.my_text)
        v_lay.addWidget(descr)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.close()