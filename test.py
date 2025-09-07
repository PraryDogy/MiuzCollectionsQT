import os
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt, QThreadPool, QObject, pyqtSignal
from system.tasks import LoadDirsTask

class MyTree(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.threadpool = QThreadPool()
        self.itemClicked.connect(self.on_item_click)
        self.first_load()

    def first_load(self):
        root_path = "/Users/pupitor9000/Downloads"
        root_item = QTreeWidgetItem([os.path.basename(root_path)])
        root_item.setData(0, Qt.UserRole, root_path)
        self.addTopLevelItem(root_item)

        # заглушка, если есть подпапки
        worker = LoadDirsTask(root_path)
        worker.sigs.finished_.connect(lambda data, item=root_item: self.add_children(item, data))
        self.threadpool.start(worker)

    def on_item_click(self, item, col):
        # если у узла ещё нет детей
        if item.childCount() == 0:
            path = item.data(0, Qt.UserRole)
            worker = LoadDirsTask(path)
            worker.sigs.finished_.connect(lambda data, item=item: self.add_children(item, data))
            self.threadpool.start(worker)
        item.setExpanded(True)

    def add_children(self, parent_item, data: dict):
        parent_item.takeChildren()  # удаляем заглушку
        for path, name in data.items():
            child = QTreeWidgetItem([name])
            child.setData(0, Qt.UserRole, path)
            parent_item.addChild(child)


if __name__ == "__main__":
    import sys
    from PyQt5.QtCore import QRunnable
    app = QApplication(sys.argv)
    tree = MyTree()
    tree.show()
    sys.exit(app.exec_())
