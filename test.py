import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QThread
import time

class NewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Новое окно')
        self.setGeometry(100, 100, 200, 100)
        label = QLabel('Это новое окно', self)
        centralWidget = QWidget()
        layout = QVBoxLayout(centralWidget)
        layout.addWidget(label)
        self.setCentralWidget(centralWidget)

class Worker(QThread):
    def run(self):
        count = 0
        while True:
            print(count)
            count += 1
            time.sleep(1)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Главное окно')
        self.setGeometry(100, 100, 300, 200)

        centralWidget = QWidget()
        self.layout = QVBoxLayout(centralWidget)

        self.openWindowButton = QPushButton('Открыть новое окно', self)
        self.openWindowButton.clicked.connect(self.openNewWindow)
        self.layout.addWidget(self.openWindowButton)

        self.restartButton = QPushButton('Перезапустить GUI', self)
        self.restartButton.clicked.connect(self.restartGUI)
        self.layout.addWidget(self.restartButton)

        self.startThreadButton = QPushButton('Запустить поток', self)
        self.startThreadButton.clicked.connect(self.startThread)
        self.layout.addWidget(self.startThreadButton)

        self.setCentralWidget(centralWidget)

    def openNewWindow(self):
        self.newWindow = NewWindow()
        self.newWindow.show()

    def restartGUI(self):
        print("restart gui")
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        self.initUI()

    def startThread(self):
        self.worker = Worker()
        self.worker.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
