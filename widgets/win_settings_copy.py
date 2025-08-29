from copy import deepcopy

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QPushButton, QSplitter, QTextEdit, QWidget

from cfg import JsonData, Static
from system.lang import Lang
from system.main_folder import MainFolder
from system.utils import MainUtils

from ._base_widgets import UHBoxLayout, UListWidgetItem, VListWidget, WinChild


class WinSettings(WinChild):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.main_folder_list = deepcopy(MainFolder.list_)
        self.json_data = deepcopy(JsonData)


        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.central_layout.addWidget(self.splitter)

        self.left_menu = VListWidget()
        self.splitter.addWidget(self.left_menu)

        for i in MainFolder.list_:
            item = UListWidgetItem(self.left_menu, text=i.name)
            self.left_menu.addItem(item)

        self.left_menu.setCurrentRow(0)

        self.right_wid = QWidget()
        self.splitter.addWidget(self.right_wid)

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([Static.MENU_LEFT_WIDTH, 600])

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)