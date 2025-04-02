from PyQt5.QtWidgets import QApplication, QMainWindow, QTabBar, QVBoxLayout, QWidget, QPushButton, QMenu
from PyQt5.QtCore import Qt
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setFixedSize(300, 100)  # Фиксированное окно шириной 300px

        # Создаем центральный виджет и layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.tab_bar = QTabBar(self)

        self.show_tabs_button = QPushButton("Показать все вкладки", self)
        self.show_tabs_button.setVisible(False)
        self.show_tabs_button.clicked.connect(self.show_all_tabs)

        layout.addWidget(self.tab_bar)
        layout.addWidget(self.show_tabs_button)

        self.tabs = []

    def add_tab(self, tab_name):

        if len(self.tabs) >= 3:
            self.show_tabs_button.setVisible(True)
        else:
            self.tab_bar.addTab(tab_name)

        self.tabs.append(tab_name)

    def show_all_tabs(self):
        menu = QMenu(self)
        for tab in self.tabs:
            action = menu.addAction(tab)
            # action.triggered.connect(
            #     lambda checked, tab=tab: self.switch_to_tab(tab)
            # )
        menu.exec_(self.show_tabs_button.mapToGlobal(self.show_tabs_button.rect().bottomLeft()))

    def switch_to_tab(self, tab_name):
        # Можно добавить логику для переключения на вкладку по имени
        index = self.tabs.index(tab_name)
        self.tab_bar.setCurrentIndex(index)

app = QApplication(sys.argv)
window = MainWindow()

# Добавляем вкладки
window.add_tab("Вкладка 1")
window.add_tab("Вкладка 2")
window.add_tab("Вкладка 3")
window.add_tab("Вкладка 4")

window.show()
sys.exit(app.exec_())
