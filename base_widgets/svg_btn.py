from PyQt5.QtSvg import QSvgWidget
import os

class SvgBtn(QSvgWidget):
    def __init__(self, icon_name: str, size: int):
        super().__init__(os.path.join("images", icon_name))
        self.setFixedSize(size, size)

    def set_icon(self, icon_name):
        self.load(os.path.join("images", icon_name))
