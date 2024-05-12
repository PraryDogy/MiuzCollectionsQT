from typing import Literal

from PyQt5.QtWidgets import QSpacerItem, QWidget

from base_widgets import Btn, LayoutH
from cfg import cnf
from styles import Names, default_theme


class ThumbMove(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout_h = LayoutH()
        self.setLayout(layout_h)

        self.move_jpg = cnf.move_jpg
        self.move_layers = cnf.move_layers

        size = (60, 17)

        self.btn_jpg = Btn("JPG")
        self.btn_jpg.setFixedSize(*size)
        self.btn_jpg.mouseReleaseEvent = lambda f: self.btn_cmd("jpg")
        layout_h.addWidget(self.btn_jpg)
        self.jpg_btn_style()

        layout_h.addSpacerItem(QSpacerItem(1, 0))

        self.btn_tiff = Btn(cnf.lng.layers)
        self.btn_tiff.setFixedSize(*size)
        self.btn_tiff.mouseReleaseEvent = lambda f: self.btn_cmd("tiff")        
        layout_h.addWidget(self.btn_tiff)
        self.tiff_btn_style()

    def btn_cmd(self, flag: Literal["jpg", "tiff"]):
        if flag == "jpg":
            self.move_jpg = not self.move_jpg
            cnf.move_jpg = self.move_jpg
            self.jpg_btn_style()

        elif flag == "tiff":
            self.move_layers = not self.move_layers
            cnf.move_layers = self.move_layers
            self.tiff_btn_style()

    def jpg_btn_style(self):
        if cnf.move_jpg:
            self.btn_jpg.setObjectName(Names.st_bar_jpg_sel)
        else:
            self.btn_jpg.setObjectName(Names.st_bar_jpg)

        self.btn_jpg.setStyleSheet(default_theme)

    def tiff_btn_style(self):
        if cnf.move_layers:
            self.btn_tiff.setObjectName(Names.st_bar_tiff_sel)
        else:
            self.btn_tiff.setObjectName(Names.st_bar_tiff)
        
        self.btn_tiff.setStyleSheet(default_theme)