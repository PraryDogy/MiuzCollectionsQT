from typing import Literal

from PyQt5.QtWidgets import QSpacerItem, QWidget

from base_widgets import Btn, LayoutH
from cfg import cnf
from signals import gui_signals_app
from styles import Styles


class ThumbMove(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout_h = LayoutH()
        self.setLayout(layout_h)

        self.move_jpg = cnf.move_jpg
        self.move_layers = cnf.move_layers

        size = (60, 17)

        self.btn_jpg = Btn("JPG")
        self.btn_jpg.setStyleSheet(self.get_jpg_style())
        self.btn_jpg.setFixedSize(*size)
        self.btn_jpg.mouseReleaseEvent = lambda f: self.btn_cmd("jpg")
        layout_h.addWidget(self.btn_jpg)

        layout_h.addSpacerItem(QSpacerItem(1, 0))

        self.btn_tiff = Btn(cnf.lng.layers)
        self.btn_tiff.setFixedSize(*size)
        self.btn_tiff.mouseReleaseEvent = lambda f: self.btn_cmd("tiff")
        self.btn_tiff.setStyleSheet(self.get_tiff_style())
        
        layout_h.addWidget(self.btn_tiff)


    def btn_cmd(self, flag: Literal["jpg", "tiff"]):
        if flag == "jpg":
            self.move_jpg = not self.move_jpg
            cnf.move_jpg = self.move_jpg
            self.btn_jpg.setStyleSheet(self.get_jpg_style())
        
        elif flag == "tiff":
            self.move_layers = not self.move_layers
            cnf.move_layers = self.move_layers
            self.btn_tiff.setStyleSheet(self.get_tiff_style())

    def get_bg(self, flag: Literal["jpg", "tiff"]):
        if flag == "jpg":
            return Styles.st_bar_sel if self.move_jpg else Styles.btn_base_color
        
        elif flag == "tiff":
            return Styles.st_bar_sel if self.move_layers else Styles.btn_base_color

    def get_jpg_style(self):
        return f"""
                background: {self.get_bg("jpg")};
                border-top-left-radius: {Styles.small_radius}px;
                border-bottom-left-radius: {Styles.small_radius}px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                """

    def get_tiff_style(self):
        return f"""
                background: {self.get_bg("tiff")};
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: {Styles.small_radius}px;
                border-bottom-right-radius: {Styles.small_radius}px;
                """