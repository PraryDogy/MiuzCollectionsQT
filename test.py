import os

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem


class TreeWid(QTreeWidget):
    tree_reveal = pyqtSignal(str)
    tree_open = pyqtSignal(str)

    svg_folder = "./images/folder.svg"
    svg_size = 16
    item_height = 25

    def __init__(self, paths: list[str]):
        super().__init__()
        self.selected_path: str = None
        self.items: dict[str, QTreeWidgetItem] = {}

        self.setHeaderHidden(True)
        self.setAutoScroll(False)
        self.setIconSize(QSize(self.svg_size, self.svg_size))
        self.setIndentation(15)

        root_item = self.init_ui()
        self.build_tree(root_item, paths)

    # --- построение ---
    def init_ui(self):
        root_item = QTreeWidgetItem(["TEST"])
        root_item.setSizeHint(0, QSize(0, self.item_height))
        root_item.setData(0, Qt.ItemDataRole.UserRole, os.sep)
        root_item.setIcon(0, QIcon(self.svg_folder))
        self.addTopLevelItem(root_item)
        return root_item

    def build_tree(self, root_item: QTreeWidgetItem, paths: list[str]) -> None:
        self.items = {os.sep: root_item}

        for full_path in sorted(paths):
            full_path = os.path.normpath(full_path)

            parts = full_path.split(os.sep)
            current_path = ""

            for part in parts:
                if not part:
                    current_path = os.sep
                    continue

                current_path = os.path.join(current_path, part)

                if current_path not in self.items:
                    parent_path = os.path.dirname(current_path) or os.sep
                    parent_item = self.items.get(parent_path)
                    if parent_item is None:
                        continue

                    item = QTreeWidgetItem([part])
                    item.setIcon(0, QIcon(self.svg_folder))
                    item.setSizeHint(0, QSize(0, self.item_height))
                    item.setData(0, Qt.UserRole, current_path)

                    parent_item.addChild(item)
                    self.items[current_path] = item

        root_item.setExpanded(True)
        if paths:
            last_path = max(paths, key=len)  # самый глубокий
            self.expand_to_path(last_path)

    def expand_to_path(self, path: str):
        if not path or path not in self.items:
            return

        item = self.items[path]

        while item:
            item.setExpanded(True)
            item = item.parent()

        self.setCurrentItem(self.items[path])
        self.scrollToItem(self.items[path], QTreeWidget.PositionAtCenter)

# from PyQt5.QtWidgets import QApplication

# paths = ["/Users/evlosh/Desktop",]
# app = QApplication([])
# wid = TreeWid(paths)
# wid.show()
# app.exec()