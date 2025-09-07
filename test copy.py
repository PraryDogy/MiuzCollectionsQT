import os
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt


class MyTree(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.itemClicked.connect(self.on_item_click)
        self.first_load()

    def first_load(self):
        root_path = "/Users/pupitor9000/Downloads"
        root_item = QTreeWidgetItem([os.path.basename(root_path)])   # показываем только имя
        root_item.setData(0, Qt.UserRole, root_path)                 # полный путь спрятан
        self.addTopLevelItem(root_item)

    def load_subdirs(self, parent_item, path):
        try:
            for entry in os.scandir(path):
                if entry.is_dir():
                    child = QTreeWidgetItem([entry.name])            # имя папки
                    child.setData(0, Qt.UserRole, entry.path)        # полный путь в data
                    parent_item.addChild(child)
        except PermissionError:
            pass

    def on_item_click(self, item, col):
        if item.childCount() == 0:
            path = item.data(0, Qt.UserRole)
            self.load_subdirs(item, path)
        item.setExpanded(True)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    tree = MyTree()
    tree.show()
    sys.exit(app.exec_())
