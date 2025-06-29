import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QLabel, QPushButton, QSpacerItem, QWidget

from cfg import JsonData, Static
from system.lang import Lang

from ._base_widgets import SvgBtn, UHBoxLayout, UVBoxLayout, WinSystem


class WinFirstLoad(WinSystem):
    yes_pressed = pyqtSignal()
    no_pressed = pyqtSignal()

    def __init__(self, question: str):
        super().__init__()
        self.central_layout.setContentsMargins(10, 5, 10, 5)
        self.central_layout.setSpacing(5)

        btn_wid_ = self.btn_wid()
        self.central_layout.insertWidget(1, btn_wid_)

        self.current_page = 0
        self.max_pages = 2
        self.page_list = [
            lambda: self.create_page(Lang.page_one, 0),
            lambda: self.create_page(Lang.page_one, 1),
            lambda: self.create_page(Lang.page_two, 2)
        ]

        self.dynamic_wid = self.page_list[0]()
        self.central_layout.insertWidget(0, self.dynamic_wid)
        self.adjustSize()

    def create_page(self, text: str, page_num: int):
        v_wid = QWidget()
        v_lay = UVBoxLayout()
        v_lay.setSpacing(10)
        v_wid.setLayout(v_lay)

        descr = QLabel(text)
        v_lay.addWidget(descr)

        svg = self.get_svg_name(page_num)
        svg = os.path.join(Static.images_dir, svg)

        print(svg)

        svg_wid = QSvgWidget()
        svg_wid.load(svg)
        svg_wid.setFixedSize(svg_wid.sizeHint())
        v_lay.addWidget(svg_wid, alignment=Qt.AlignmentFlag.AlignCenter)

        return v_wid

    def btn_wid(self):
        btn_wid = QWidget()
        btn_lay = UHBoxLayout()
        btn_lay.setSpacing(10)
        btn_wid.setLayout(btn_lay)

        btn_lay.addStretch()

        self.back_btn = QPushButton("Назад")
        self.back_btn.setFixedWidth(100)
        btn_lay.addWidget(self.back_btn)

        self.next_btn = QPushButton("Далее")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setFixedWidth(100)
        btn_lay.addWidget(self.next_btn)

        btn_lay.addStretch()

        return btn_wid
    
    def next_page(self):
        self.current_page += 1
        if self.current_page > self.max_pages:
            self.current_page -= 1
            self.next_btn.setDisabled(True)
        else:
            self.dynamic_wid.deleteLater()
            new_wid = self.page_list[self.current_page]
            self.dynamic_wid = new_wid()
            self.central_layout.insertWidget(1, self.dynamic_wid)

    def get_svg_name(self, number: int):
        return f"example {number} {JsonData.lang_ind}.svg"
    
    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
