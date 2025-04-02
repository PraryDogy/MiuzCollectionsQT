from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QMenu, QMenuBar, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("QTabWidget with QMenu")
        self.setGeometry(100, 100, 600, 400)

        tab_widget = QTabWidget(self)
        self.setCentralWidget(tab_widget)

        first = QLabel("first tab")
        tab_widget.addTab(first, "first")

        test = QWidget()
        tab_widget.addTab(test, "test")

        # # Создание QMenu
        # menu = QMenu(self)
        # menu.addAction("Action 1")
        # menu.addAction("Action 2")
        # menu.addAction("Action 3")

        # def show_menu():
        #     menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))

        # button.clicked.connect(show_menu)
        # layout.addWidget(button)

        # tab_widget.addTab(menu_tab, "Menu Tab")

app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
