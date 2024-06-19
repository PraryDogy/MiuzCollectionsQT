import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Main Window')
        self.setGeometry(100, 100, 800, 600)
        
        self.reveal_file_button = QPushButton('Reveal File in Finder', self)
        self.reveal_file_button.clicked.connect(self.reveal_file)
        self.reveal_file_button.enterEvent = lambda e: self.test()
        
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.reveal_file_button)
        
        self.setCentralWidget(central_widget)

    def test(self):
        self.reveal_file_button.setToolTip("hello")

    def reveal_file(self):
        os.system('open .')
        QTimer.singleShot(500, self.restore_focus)

    def restore_focus(self):
        self.raise_()
        # self.reveal_file_button.setFocus()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
