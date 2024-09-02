from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QListView, QVBoxLayout, QWidget, QScroller, QScrollerProperties
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class BounceScrollApp(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        # Создаем QListView как пример
        self.list_view = QListView()
        layout.addWidget(self.list_view)

        # Модель данных для примера
        model = QStandardItemModel()
        for i in range(50):
            item = QStandardItem(f'Item {i + 1}')
            model.appendRow(item)
        self.list_view.setModel(model)

        # Включаем отскакивание при скроллинге
        scroller = QScroller.scroller(self.list_view.viewport())
        scroller.grabGesture(self.list_view.viewport(), QScroller.LeftMouseButtonGesture)

        # Настройка поведения скроллинга через QScrollerProperties
        properties = scroller.scrollerProperties()
        properties.setScrollMetric(QScrollerProperties.OvershootDragResistanceFactor, 0.5)
        properties.setScrollMetric(QScrollerProperties.OvershootScrollDistanceFactor, 0.3)
        properties.setScrollMetric(QScrollerProperties.OvershootScrollTime, 0.5)
        scroller.setScrollerProperties(properties)

        self.setLayout(layout)
        self.setWindowTitle('Bounce Scroll Example')
        self.setGeometry(300, 300, 300, 400)

if __name__ == '__main__':
    app = QApplication([])
    window = BounceScrollApp()
    window.show()
    app.exec_()
