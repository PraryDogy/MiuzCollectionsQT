import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QFileDialog, QLabel, QMainWindow, QPushButton,
                             QSpacerItem, QVBoxLayout, QWidget)

from base_widgets import Btn, LayoutH, LayoutV, WinStandartBase
from utils import MainUtils


class Manager:
    coll_folder = "123"


class BrowseColl(QWidget):
    chanded = pyqtSignal()
    text_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        main_layout = LayoutH()
        self.setLayout(main_layout)

        self.browse_btn = Btn("Обзор")
        self.browse_btn.mouseReleaseEvent = self.choose_folder
        main_layout.addWidget(self.browse_btn)

        main_layout.addSpacerItem(QSpacerItem(10, 0))

        self.coll_path_label = QLabel()
        self.coll_path_label.setWordWrap(True)
        self.coll_path_label.setText(Manager.coll_folder)
        main_layout.addWidget(self.coll_path_label)

    def choose_folder(self, e):
        self.coll_path_label.setText("/Users/Loshkarev/Documents/_Projects/MiuzCollectionsQT/env/lib/python3.11/site-packages/cv2/__pycache__")

    def finalize(self):        
        ...




class WinSmb(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("title")
        self.resize(420, 120)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.init_ui()

    def init_ui(self):
        title = QLabel("123")
        self.main_layout.addWidget(title)
        self.browse_coll = BrowseColl()
        self.main_layout.addWidget(self.browse_coll)
        self.main_layout.addStretch()
        self.main_layout.addItem(QSpacerItem(0, 20))
        self.ok_btn = QPushButton("Ok")
        self.ok_btn.clicked.connect(self.ok_cmd)
        self.main_layout.addWidget(self.ok_btn, alignment=Qt.AlignCenter)

    def ok_cmd(self):
        self.close()





import sys

from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WinSmb()
    window.show()
    sys.exit(app.exec_())