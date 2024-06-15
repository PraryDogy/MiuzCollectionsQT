import sys
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

        for i in range(0, 3):
            my_grid = QWidget()
            grid_layout.addWidget(my_grid)
            my_grid_layout = QVBoxLayout()
            my_grid.setLayout(my_grid_layout)

            title = QLabel(text=f"ноябрь {i}")
            my_grid_layout.addWidget(title)

            self.widgets.append(title)

            for i in range(0, 10):
                test = QLabel(text="test")
                my_grid_layout.addWidget(test)

        # Подключаем сигналы прокрутки скроллбаров
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)

    def on_scroll(self, value):
        for title in self.widgets:
            if not self.is_widget_visible(title):
                print(f"{title.text()} is out of view")
                break

    def is_widget_visible(self, widget):
        # Получаем видимую область прокручиваемого содержимого
        visible_rect = self.scroll_area.viewport().rect()
        # Преобразуем координаты виджета относительно видимой области
        widget_rect = self.scroll_area.viewport().mapFromGlobal(widget.mapToGlobal(widget.rect().topLeft()))
        widget_geom = QRect(widget_rect, widget.size())
        
        # Проверяем пересечение областей
        return visible_rect.intersects(widget_geom)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScrollWidget()
    window.show()
    sys.exit(app.exec_())
