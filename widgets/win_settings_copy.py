from copy import deepcopy

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QSplitter, QWidget, QLabel

from cfg import JsonData, Static
from system.lang import Lang
from system.main_folder import MainFolder
from ._base_widgets import UVBoxLayout

from ._base_widgets import UListWidgetItem, VListWidget, WinChild


class MainSettings(QWidget):
    settings_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.v_lay = UVBoxLayout()
        self.setLayout(self.v_lay)

        lbl = QLabel("test")
        self.v_lay.addWidget(lbl)


class WinSettings(WinChild):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.main_folder_list = deepcopy(MainFolder.list_)
        self.json_data = deepcopy(JsonData)

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.central_layout.addWidget(self.splitter)

        self.left_menu = VListWidget()
        self.left_menu.mouseReleaseEvent = self.item_clicked
        self.splitter.addWidget(self.left_menu)

        main_settings_item = UListWidgetItem(self.left_menu, text=Lang.main)
        self.left_menu.addItem(main_settings_item)

        for i in MainFolder.list_:
            item = UListWidgetItem(self.left_menu, text=i.name)
            self.left_menu.addItem(item)

        self.left_menu.setCurrentRow(0)

        self.right_wid = QWidget()
        self.right_lay = UVBoxLayout()
        self.right_wid.setLayout(self.right_lay)
        self.splitter.addWidget(self.right_wid)

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([Static.MENU_LEFT_WIDTH, 600])

        self.item_clicked()

    def item_clicked(self, *args):
        for i in self.right_wid.findChildren(QWidget):
            i.deleteLater()
        curr_row = self.left_menu.currentRow()
        if curr_row == 0:
            self.main_settings = MainSettings()
            self.right_lay.addWidget(self.main_settings)
        else:
            main_folder_name = self.left_menu.currentItem().text()
            print(main_folder_name)
            

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)