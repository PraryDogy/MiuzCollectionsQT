import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLabel, QPushButton, QSpacerItem, QWidget

from base_widgets import LayoutHor, SvgBtn
from base_widgets.wins import WinChild
from lang import Lang

IMAGES = "images"
WARNING_SVG = os.path.join(IMAGES, "warning.svg")

class WinSmb(WinChild):
    def __init__(self, text: str = None):
        super().__init__()

        if text:
            self.my_text = text
        else:
            self.my_text = Lang.choose_coll_smb

        self.setWindowTitle(Lang.no_connection)

        self.init_ui()
        self.setFixedSize(330, 120)
        self.setFocus()

        self.new_coll_path = None
        self.new_lang = None
        self.need_reset = None

    def init_ui(self):
        h_wid = QWidget()
        self.content_lay_v.addWidget(h_wid)
        h_layout = LayoutHor()
        h_wid.setLayout(h_layout)

        icon_label = SvgBtn(WARNING_SVG, 40)
        h_layout.addWidget(icon_label)

        h_layout.addSpacerItem(QSpacerItem(15, 0))

        descr = QLabel(self.my_text)
        h_layout.addWidget(descr)

        h_layout.addStretch()

        self.content_lay_v.addSpacerItem(QSpacerItem(0, 10))

        self.ok_btn = QPushButton(text=Lang.ok)
        self.ok_btn.setFixedWidth(90)
        self.ok_btn.clicked.connect(self.close)
        self.content_lay_v.addWidget(self.ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Return, Qt.Key.Key_Escape):
            self.close()