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

        main_layout = LayoutV()
        self.setLayout(main_layout)

        descr = QLabel("123")
        main_layout.addWidget(descr)

        main_layout.addSpacerItem(QSpacerItem(0, 15))

        self.h_wid = QWidget()
        main_layout.addWidget(self.h_wid)

        h_layout = LayoutH()
        self.h_wid.setLayout(h_layout)

        self.browse_btn = Btn("Обзор")
        self.browse_btn.mouseReleaseEvent = self.choose_folder
        h_layout.addWidget(self.browse_btn)

        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.coll_path_label = QLabel()
        self.coll_path_label.setWordWrap(True)
        self.coll_path_label.setText(Manager.coll_folder)
        h_layout.addWidget(self.coll_path_label)


    def choose_folder(self, e):
        file_dialog = QFileDialog()
        file_dialog.setOption(QFileDialog.ShowDirsOnly, True)

        selected_folder = file_dialog.getExistingDirectory()

        if selected_folder:
            Manager.coll_folder = selected_folder
            self.coll_path_label.setText(Manager.coll_folder)

        print(self.height())
        self.coll_path_label.adjustSize()
        self.adjustSize()
        self.text_changed.emit()
        print(self.height())

    def finalize(self):        
        ...




class WinSmb(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("title")
        self.setMinimumSize(320, 100)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.init_ui()

    def init_ui(self):
        self.browse_coll = BrowseColl()

        self.main_layout.addWidget(self.browse_coll)

        self.main_layout.addItem(QSpacerItem(0, 20))

        self.ok_btn = QPushButton("Ok")
        self.ok_btn.clicked.connect(self.ok_cmd)
        self.main_layout.addWidget(self.ok_btn, alignment=Qt.AlignCenter)

        self.browse_coll.text_changed.connect(self.test)

    def ok_cmd(self):
        # self.browse_coll.finalize()
        print("finalize disabled")

        self.close()

    def keyPressEvent(self, event):
        event.ignore()

    def test(self):
        print(1)




import sys

from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WinSmb()
    window.show()
    sys.exit(app.exec_())