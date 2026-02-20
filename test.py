import os

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QGroupBox, QLabel, QTreeWidget, QTreeWidgetItem,
                             QWidget)

from cfg import cfg
from system.lang import Lng
from widgets._base_widgets import (SingleActionWindow, SmallBtn, UHBoxLayout,
                                   UVBoxLayout)


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
        self.setIndentation(10)
        self.build_tree(paths)

    def build_tree(self, paths: list[str]) -> None:
        self.clear()
        self.items = {}

        for full_path in sorted(paths):
            full_path = os.path.normpath(full_path)
            parts = full_path.split(os.sep)

            current_path = ""
            parent_item = None

            for part in parts:
                if part == "":
                    current_path = os.sep
                    continue

                if current_path == os.sep:
                    current_path = os.path.join(os.sep, part)
                else:
                    current_path = os.path.join(current_path, part)

                if current_path not in self.items:
                    item = QTreeWidgetItem([part])
                    item.setIcon(0, QIcon(self.svg_folder))
                    item.setSizeHint(0, QSize(0, self.item_height))
                    item.setData(0, Qt.UserRole, current_path)

                    if parent_item:
                        parent_item.addChild(item)
                    else:
                        self.addTopLevelItem(item)

                    self.items[current_path] = item

                parent_item = self.items[current_path]

        if paths:
            last_path = max(paths, key=len)
            self.expand_to_path(os.path.normpath(last_path))

    def expand_to_path(self, path: str):
        path = os.path.normpath(path)
        item = self.items.get(path)
        if not item:
            return

        while item:
            item.setExpanded(True)
            item = item.parent()

        self.setCurrentItem(self.items[path])
        self.scrollToItem(self.items[path], QTreeWidget.PositionAtCenter)


class UploadWin(SingleActionWindow):
    ok_clicked = pyqtSignal()

    def __init__(self, paths: list[str]):
        super().__init__()
        self.setWindowTitle(Lng.upload_in[cfg.lng])
        self.setFixedSize(400, 400)
        self.central_layout.setSpacing(10)

        group = QGroupBox()
        self.central_layout.addWidget(group)

        group_lay = UVBoxLayout()
        group.setLayout(group_lay)

        descr = QLabel(Lng.upload_descr[cfg.lng])
        group_lay.addWidget(descr)

        tree = TreeWid(paths)
        self.central_layout.addWidget(tree)

        btn_wid = QWidget()
        self.central_layout.addWidget(btn_wid)
        btn_lay = UHBoxLayout()
        btn_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_lay.setSpacing(10)
        btn_wid.setLayout(btn_lay)

        ok_btn = SmallBtn(Lng.ok[cfg.lng])
        ok_btn.clicked.connect(self.ok_clicked)
        ok_btn.setFixedWidth(90)
        btn_lay.addWidget(ok_btn)

        cancel_btn = SmallBtn(Lng.cancel[cfg.lng])
        cancel_btn.clicked.connect(self.deleteLater)
        cancel_btn.setFixedWidth(90)
        btn_lay.addWidget(cancel_btn)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        elif a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.ok_clicked.emit()
        return super().keyPressEvent(a0)