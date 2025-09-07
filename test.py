import os
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt, QThreadPool, QObject, pyqtSignal
from system.tasks import LoadDirsTask
import os
from typing import Dict
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal, QThreadPool


class MyTree(QTreeWidget):
    clicked_: pyqtSignal = pyqtSignal(str)

    def __init__(self, root_dir: str) -> None:
        super().__init__()
        self.setHeaderHidden(True)
        self.threadpool: QThreadPool = QThreadPool()
        self.itemClicked.connect(self.on_item_click)

        root_item: QTreeWidgetItem = QTreeWidgetItem([os.path.basename(root_dir)])
        root_item.setData(0, Qt.ItemDataRole.UserRole, root_dir)  # полный путь
        self.addTopLevelItem(root_item)

        worker: LoadDirsTask = LoadDirsTask(root_dir)
        worker.sigs.finished_.connect(lambda data, item=root_item: self.add_children(item, data))
        self.threadpool.start(worker)

    def on_item_click(self, item: QTreeWidgetItem, col: int) -> None:
        path: str = item.data(0, Qt.ItemDataRole.UserRole)
        self.clicked_.emit(path)
        if item.childCount() == 0:
            worker: LoadDirsTask = LoadDirsTask(path)
            worker.sigs.finished_.connect(lambda data, item=item: self.add_children(item, data))
            self.threadpool.start(worker)
        item.setExpanded(True)

    def add_children(self, parent_item: QTreeWidgetItem, data: Dict[str, str]) -> None:
        parent_item.takeChildren()  # удаляем заглушку
        for path, name in data.items():
            child: QTreeWidgetItem = QTreeWidgetItem([name])
            child.setData(0, Qt.ItemDataRole.UserRole, path)  # полный путь
            parent_item.addChild(child)



if __name__ == "__main__":
    import sys
    from PyQt5.QtCore import QRunnable
    src = "/Users/pupitor9000/Downloads"
    app = QApplication(sys.argv)
    tree = MyTree(src)
    tree.show()
    sys.exit(app.exec_())
