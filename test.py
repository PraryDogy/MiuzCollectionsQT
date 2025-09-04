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
        

class PageTwo(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)

        # Корневая папка
        folder_item = QTreeWidgetItem(self, [Lng.collection_folder[JsonData.lng]])

        # Добавляем изображения напрямую в папку
        for i in range(1, 11):  # четыре изображения
            QTreeWidgetItem(folder_item, [f"{Lng.image[JsonData.lng]} {i}"])

        self.expandAll()
        self.setFixedSize(500, 500)


class PageThree(QTreeWidget):
    filters = (
        "1 IMG",
        "2 MODEL IMG"
    )
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)

        # Корневая папка
        folder_item = QTreeWidgetItem(self, [Lng.collection_folder[JsonData.lng]])

        # Коллекция
        collection_item = QTreeWidgetItem(folder_item, [f"{Lng.collection[JsonData.lng]} 1"])

        # 1 IMG
        img1_item = QTreeWidgetItem(collection_item, [self.filters[0]])
        for i in range(1, 4):
            QTreeWidgetItem(img1_item, [f"{Lng.image[JsonData.lng]} {i}"])

        # 2 MODEL IMG
        img2_item = QTreeWidgetItem(collection_item, [self.filters[1]])
        for i in range(1, 4):
            QTreeWidgetItem(img2_item, [f"{Lng.image[JsonData.lng]} {i}"])

        # Любая другая папка
        other_folder_item = QTreeWidgetItem(folder_item, [f"{Lng.other_folders[JsonData.lng]}"])
        for i in range(1, 4):
            QTreeWidgetItem(other_folder_item, [f"{Lng.image[JsonData.lng]} {i}"])

        self.expandAll()
        self.setFixedSize(500, 500)



app = QApplication([])
page = PageThree()
page.adjustSize()
page.show()
app.exec_()
