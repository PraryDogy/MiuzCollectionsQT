import os
import sys

from PyQt5.QtCore import Qt,  pyqtSignal
from PyQt5.QtWidgets import QApplication, QListWidget, QWidget

from widgets._base_widgets import UListWidgetItem
from system.tasks import LoadDirsTask


class UploadListItem(UListWidgetItem):
    def __init__(self, parent, path: str, height = 30, text = None):
        super().__init__(parent, height, text)
        self.path = path


class UploadListWidget(QListWidget):
    clicked = pyqtSignal(str)

    def __init__(self, paths: dict[str, str]):
        super().__init__()
        self.paths = paths

    def init_ui(self):
        for path, name in self.paths.items():
            item = UploadListItem(parent=self, path=path, text=name)
            self.addItem(item)

    def currentItem(self) -> UploadListItem:
        return super().currentItem()

    def mouseReleaseEvent(self, e):
        if not e.button() == Qt.MouseButton.LeftButton:
            return

        item = self.currentItem()
        if item:
            self.clicked.emit(item.path)

        return super().mouseReleaseEvent(e)


class UploadWin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setFixedSize(500, 500)