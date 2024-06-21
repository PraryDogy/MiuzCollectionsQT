from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Main Window')
        self.setGeometry(100, 100, 400, 300)

        button = QPushButton('Open Modal Window', self)
        button.clicked.connect(self.openModalWindow)
        self.setCentralWidget(button)

    def openModalWindow(self):
        self.modalWindow = ModalWindow(self)
        self.modalWindow.setWindowModality(Qt.ApplicationModal)
        self.modalWindow.show()

class ModalWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Modal Window')
        self.setGeometry(150, 150, 200, 100)

        self.child_windows = []  # Список для хранения дочерних окон

        layout = QVBoxLayout()
        button1 = QPushButton('Open Child Window 1', self)
        button1.clicked.connect(lambda: self.openChildWindow('Child Window 1'))
        layout.addWidget(button1)

        button2 = QPushButton('Open Child Window 2', self)
        button2.clicked.connect(lambda: self.openChildWindow('Child Window 2'))
        layout.addWidget(button2)

        self.setLayout(layout)

    def openChildWindow(self, title):
        child_window = ChildWindow(self, title)
        child_window.show()
        self.child_windows.append(child_window)  # Сохраняем ссылку на дочернее окно

class ChildWindow(QWidget):
    def __init__(self, parent=None, title=''):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 150, 100)
        layout = QVBoxLayout()
        label = QLabel(f'This is {title}', self)
        layout.addWidget(label)
        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication([])
    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()
