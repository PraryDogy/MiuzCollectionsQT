import sys
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout
from PyQt5.QtCore import QThreadPool, QRunnable, pyqtSlot
from system.tasks import ScanerSingleDir
from system.utils import UThreadPool
from system.main_folder import MainFolder
from system.database import Dbase

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.pool = QThreadPool()
        btn = QPushButton("Запустить задачу")
        btn.clicked.connect(self.run_task)
        layout = QVBoxLayout(self)
        layout.addWidget(btn)

    def run_task(self):
        UThreadPool.init()
        Dbase.init()
        src = "/Users/pupitor9000/Downloads/collections/new"
        main_folder = MainFolder(name="aaa", paths=[src, ], curr_path=src)
        self.task = ScanerSingleDir(main_folder, src)
        UThreadPool.start(self.task)

app = QApplication(sys.argv)
w = Window()
w.show()
sys.exit(app.exec_())
