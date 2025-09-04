import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QLabel, QPushButton, QWidget

from cfg import JsonData, Static
from system.lang import Lng

from ._base_widgets import UHBoxLayout, UVBoxLayout, WinSystem


class WinHelp(WinSystem):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lng.win_manual[JsonData.lng])
        self.central_layout.setContentsMargins(10, 5, 10, 5)
        self.central_layout.setSpacing(5)

        btn_wid_ = self.btn_wid()
        self.central_layout.insertWidget(1, btn_wid_)

        self.current_page = 0
        self.max_pages = 2
        self.page_list = [
            lambda: self.create_page(Lng.page_one[JsonData.lng], 0),
            lambda: self.create_page(Lng.page_one[JsonData.lng], 1),
            lambda: self.create_page(Lng.page_two[JsonData.lng], 2)
        ]

        self.dynamic_wid = self.page_list[0]()
        self.central_layout.insertWidget(0, self.dynamic_wid)
        self.adjustSize()
        self.setFixedSize(480, 320)

    def create_page(self, text: str, page_num: int):
        v_wid = QWidget()
        v_lay = UVBoxLayout()
        v_lay.setSpacing(10)
        v_wid.setLayout(v_lay)

        descr = QLabel(text)
        v_lay.addWidget(descr)

        svg = f"example {page_num} {JsonData.lng}.svg"
        svg = os.path.join(Static.INNER_IMAGES, svg)

        svg_wid = QSvgWidget()
        svg_wid.load(svg)
        svg_wid.setFixedSize(svg_wid.sizeHint())
        v_lay.addWidget(svg_wid, alignment=Qt.AlignmentFlag.AlignCenter)

        v_lay.addStretch()

        return v_wid

    def btn_wid(self):
        btn_wid = QWidget()
        btn_lay = UHBoxLayout()
        btn_lay.setSpacing(10)
        btn_wid.setLayout(btn_lay)

        btn_lay.addStretch()

        self.prev_btn = QPushButton(Lng.back[JsonData.lng])
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setFixedWidth(100)
        btn_lay.addWidget(self.prev_btn)

        self.next_btn = QPushButton(Lng.next[JsonData.lng])
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setFixedWidth(100)
        btn_lay.addWidget(self.next_btn)

        btn_lay.addStretch()

        return btn_wid
    
    def next_page(self):
        self.current_page += 1
        if self.current_page > self.max_pages:
            self.current_page -= 1

        if self.current_page == self.max_pages:
            self.next_btn.setDisabled(True)

        self.prev_btn.setDisabled(False)
        self.dynamic_wid.deleteLater()
        new_wid = self.page_list[self.current_page]
        self.dynamic_wid = new_wid()
        self.central_layout.insertWidget(1, self.dynamic_wid)

    def prev_page(self):
        self.current_page -= 1
        if self.current_page < 0:
            self.current_page += 1

        if self.current_page == 0:
            self.prev_btn.setDisabled(True)

        self.next_btn.setDisabled(False)
        self.dynamic_wid.deleteLater()
        new_wid = self.page_list[self.current_page]
        self.dynamic_wid = new_wid()
        self.central_layout.insertWidget(1, self.dynamic_wid)
    
    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
