import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar,
    QComboBox, QLabel
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Image Catalog")
        self.resize(700, 400)

        self.catalogs = {
            "Photos": "/home/user/Photos",
            "Work": "/home/user/Work",
            "Projects": "/home/user/Projects",
        }

        toolbar = QToolBar()
        self.addToolBar(toolbar)

        self.catalog_combo = QComboBox()

        for name, path in self.catalogs.items():
            self.catalog_combo.addItem(name, path)

        self.catalog_combo.currentIndexChanged.connect(
            self.catalog_selected
        )

        toolbar.addWidget(self.catalog_combo)

        # Просто для демонстрации
        self.info = QLabel("Каталог: Photos")
        self.setCentralWidget(self.info)

    def catalog_selected(self, index):
        name = self.catalog_combo.currentText()
        path = self.catalog_combo.itemData(index)

        self.info.setText(
            f"Каталог: {name}\n"
            f"Путь: {path}"
        )

        # Здесь:
        # self.folder_model.setRootPath(path)
        # self.image_model.setCatalog(path)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())