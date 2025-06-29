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

        self.dynamic_page = self.page_zero()
        self.central_layout.addWidget(self.dynamic_page)

        btn_wid_ = self.btn_wid()
        self.central_layout.addWidget(btn_wid_)

        self.central_layout.addStretch()

        self.current_page = 0
        self.max_pages = 2
        self.page_list = [self.page_zero, self.page_one, self.page_two]
        

        self.adjustSize()

    def page_zero(self):
        v_wid = QWidget()
        v_lay = UVBoxLayout()
        v_lay.setSpacing(10)
        v_wid.setLayout(v_lay)

        descr = QLabel(Lang.page_one_sec)
        v_lay.addWidget(descr)

        svg = self.get_svg_name(0)
        svg = os.path.join(Static.images_dir, svg)
        svg_wid = QSvgWidget()
        svg_wid.load(svg)
        svg_wid.setFixedSize(svg_wid.sizeHint())
        v_lay.addWidget(svg_wid, alignment=Qt.AlignmentFlag.AlignCenter)

        return v_wid

    def page_one(self):
        v_wid = QWidget()
        v_lay = UVBoxLayout()
        v_lay.setSpacing(10)
        v_wid.setLayout(v_lay)

        descr = QLabel(Lang.page_one_sec)
        v_lay.addWidget(descr)

        svg = self.get_svg_name(1)
        svg = os.path.join(Static.images_dir, svg)
        svg_wid = QSvgWidget()
        svg_wid.load(svg)
        svg_wid.setFixedSize(svg_wid.sizeHint())
        v_lay.addWidget(svg_wid, alignment=Qt.AlignmentFlag.AlignCenter)

        return v_wid
    
    def page_two(self):
        v_wid = QWidget()
        v_lay = UVBoxLayout()
        v_lay.setSpacing(10)
        v_wid.setLayout(v_lay)

        descr = QLabel(Lang.page_two)
        v_lay.addWidget(descr)

        svg = self.get_svg_name(2)
        svg = os.path.join(Static.images_dir, svg)
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
            self.dynamic_page.deleteLater()
            new_wid = self.page_list[self.current_page]
            self.dynamic_page = new_wid()
            self.central_layout.insertWidget(1, self.dynamic_page)

    def get_svg_name(self, number: int):
        return f"example {number} {JsonData.lang_ind}.svg"
    
    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
