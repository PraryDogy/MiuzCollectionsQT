import sys
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QScrollArea, QPushButton, QGridLayout
from PyQt5.QtCore import Qt, QRect, QTimer

class ScrollWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.content_widget = QWidget()
        grid_layout = QVBoxLayout(self.content_widget)

        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)

        self.widgets = []
        self.widgets_coords = {}

        for i in range(0, 3):
            my_grid = QWidget()
            my_grid.setObjectName(f"ноябрь {i}")
            grid_layout.addWidget(my_grid)
            my_grid_layout = QVBoxLayout()
            my_grid.setLayout(my_grid_layout)

            title = QLabel(text=f"ноябрь {i}")
            my_grid_layout.addWidget(title)

            self.widgets.append(my_grid)

            for i in range(0, 10):
                test = QLabel(text="test")
                my_grid_layout.addWidget(test)

        # Подключаем сигналы прокрутки скроллбаров
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)

    def on_scroll(self, value):
        try:
            a = self.widgets_coords[value].objectName()
            print(a)
        except KeyError:
            print(value)

    def showEvent(self, a0: QShowEvent | None) -> None:
        for widget in self.widgets:
            self.widgets_coords[widget.y()] = widget
        print(self.widgets_coords)
        return super().showEvent(a0)
        

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = ScrollWidget()
#     window.show()
#     sys.exit(app.exec_())
