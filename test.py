from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem

from cfg import JsonData
from system.lang import Lng


class PageOne(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)

        # Корневая папка
        folder_item = QTreeWidgetItem(self, [Lng.collection_folder[JsonData.lng]])

        for i in range(1, 4):  # три подпапки
            subfolder_item = QTreeWidgetItem(
                folder_item,
                [f"{Lng.collection[JsonData.lng]} {i}"]
            )
            for j in range(1, 4):  # три изображения в каждой
                QTreeWidgetItem(
                    subfolder_item,
                    [f"{Lng.image[JsonData.lng]} {j}"]
                )

        self.expandAll()
        self.setFixedSize(500, 500)


app = QApplication([])
page = PageOne()
page.adjustSize()
page.show()
app.exec_()
