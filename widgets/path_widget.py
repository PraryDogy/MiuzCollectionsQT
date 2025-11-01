import os

from PyQt5.QtWidgets import QLabel


class PathWidget(QLabel):
    arrow = "▸"

    def __init__(self, path: str):
        super().__init__()
        self.setWordWrap(True)
        text = path.strip(os.sep).split(os.sep)
        text = f" {self.arrow} ".join(text)
        self.setText(text)
        self.path = path