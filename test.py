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

        self.widgets = []
        self.line_y_position = 100  # Y координата линии

        # Создаем 30 виджетов с подписью их номера
        for idx in range(1, 31):
            chunk_widget = QLabel(f"Widget {idx}")
            chunk_widget.setStyleSheet("background-color: lightgray; border: 1px solid black;")
            chunk_widget.setFixedHeight(100)  # Фиксированная высота виджета
            grid_layout.addWidget(chunk_widget)
            self.widgets.append(chunk_widget)

        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)

        # Линия, которая будет пересекать виджеты
        self.line = QLabel(self)
        self.line.setGeometry(0, self.line_y_position, self.width(), 2)
        self.line.setStyleSheet("background-color: red;")
        self.line.raise_()

        # Информация о пересечении линии
        self.info_label = QLabel(self)
        self.info_label.setGeometry(10, self.line_y_position - 20, 200, 20)
        self.info_label.setStyleSheet("background-color: yellow;")

        # Подключаем сигналы прокрутки скроллбаров
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.check_intersections)

        # Таймер для периодической проверки пересечений
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_intersections)
        self.timer.start(100)  # Проверка каждые 100 мс

    def check_intersections(self):
        for widget in self.widgets:
            widget_rect = self.get_widget_rect_relative_to_scroll_area(widget)
            line_rect = QRect(0, self.line_y_position, self.width(), 2)

            if widget_rect.intersects(line_rect):
                self.info_label.setText(widget.text())
                print(widget.text())
                return

        self.info_label.setText("")

    def get_widget_rect_relative_to_scroll_area(self, widget):
        widget_pos = widget.mapTo(self.scroll_area.viewport(), widget.pos())
        rect = QRect(widget_pos, widget.size())
        return rect.normalized()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScrollWidget()
    window.show()
    sys.exit(app.exec_())
