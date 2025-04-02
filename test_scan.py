import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QLabel, QVBoxLayout, QWidget, QScrollArea

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Создание QTabWidget
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        # Добавление вкладок с QLabel
        for i in range(20):
            label = QLabel(f"Контент вкладки {i+1}")
            tab_widget = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(label)
            tab_widget.setLayout(layout)
            self.tab_widget.addTab(tab_widget, f"Вкладка {i+1}")

        # Настройка прокручиваемых вкладок
        self.tab_widget.setTabBarAutoHide(False)
        self.tab_widget.setTabsClosable(False)

        # Оборачиваем QTabWidget в QScrollArea для прокрутки
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.tab_widget)
        self.setCentralWidget(scroll_area)

        # Настройка окна
        self.setWindowTitle("QTabWidget с прокруткой")
        self.setGeometry(100, 100, 300, 200)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
