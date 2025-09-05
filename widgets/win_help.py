import os

from PyQt5.QtCore import Qt
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QLabel, QPushButton, QTreeWidget, QTreeWidgetItem,
                             QWidget)

from cfg import Cfg, Static
from system.lang import Lng

from ._base_widgets import UHBoxLayout, UVBoxLayout, WinSystem


class PageOne(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)

        # Корневая папка
        folder_item = QTreeWidgetItem(self, [Lng.collection_folder[Cfg.lng]])

        for i in range(1, 4):  # три подпапки
            subfolder_item = QTreeWidgetItem(
                folder_item,
                [f"{Lng.collection[Cfg.lng]} {i}"]
            )
            for j in range(1, 4):  # три изображения в каждой
                QTreeWidgetItem(
                    subfolder_item,
                    [f"{Lng.image[Cfg.lng]} {j}"]
                )

        self.expandAll()
        

class PageTwo(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)

        # Корневая папка
        folder_item = QTreeWidgetItem(self, [Lng.collection_folder[Cfg.lng]])

        # Добавляем изображения напрямую в папку
        for i in range(1, 11):  # четыре изображения
            QTreeWidgetItem(folder_item, [f"{Lng.image[Cfg.lng]} {i}"])

        self.expandAll()


class PageThree(QTreeWidget):
    filters = (
        "1 IMG",
        "2 MODEL IMG"
    )
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)

        # Корневая папка
        folder_item = QTreeWidgetItem(self, [Lng.collection_folder[Cfg.lng]])

        # Коллекция
        collection_item = QTreeWidgetItem(folder_item, [f"{Lng.collection[Cfg.lng]} 1"])

        # 1 IMG
        img1_item = QTreeWidgetItem(collection_item, [self.filters[0]])
        for i in range(1, 4):
            QTreeWidgetItem(img1_item, [f"{Lng.image[Cfg.lng]} {i}"])

        # 2 MODEL IMG
        img2_item = QTreeWidgetItem(collection_item, [self.filters[1]])
        for i in range(1, 4):
            QTreeWidgetItem(img2_item, [f"{Lng.image[Cfg.lng]} {i}"])

        # Любая другая папка
        other_folder_item = QTreeWidgetItem(folder_item, [f"{Lng.other_folders[Cfg.lng]}"])
        for i in range(1, 4):
            QTreeWidgetItem(other_folder_item, [f"{Lng.image[Cfg.lng]} {i}"])

        self.expandAll()
        

class WinHelp(WinSystem):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lng.help[Cfg.lng])
        self.central_layout.setContentsMargins(10, 5, 10, 5)
        self.central_layout.setSpacing(15)

        descr = QLabel(Lng.help_text[Cfg.lng])
        self.central_layout.insertWidget(0, descr)

        btn_wid_ = self.btn_wid()
        self.central_layout.insertWidget(2, btn_wid_)

        self.current_page = 0
        self.max_pages = 2
        self.page_list = [
            lambda: self.create_page(PageOne, 0),
            lambda: self.create_page(PageTwo, 1),
            lambda: self.create_page(PageThree, 2)
        ]

        self.dynamic_wid = self.page_list[0]()
        self.central_layout.insertWidget(1, self.dynamic_wid)
        self.setFixedSize(450, 430)

    def create_page(self, wid: QTreeWidget, page_num: int):
        tree: QTreeWidget = wid()
        return tree

    def btn_wid(self):
        btn_wid = QWidget()
        btn_lay = UHBoxLayout()
        btn_lay.setSpacing(10)
        btn_wid.setLayout(btn_lay)

        btn_lay.addStretch()

        self.prev_btn = QPushButton(Lng.back[Cfg.lng])
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setFixedWidth(100)
        btn_lay.addWidget(self.prev_btn)

        self.next_btn = QPushButton(Lng.next_[Cfg.lng])
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setFixedWidth(100)
        btn_lay.addWidget(self.next_btn)

        btn_lay.addStretch()

        return btn_wid
    
    def next_page(self):
        self.current_page += 1
        if self.current_page > self.max_pages:
            self.current_page -= 1

        if self.current_page == self.max_pages:
            self.next_btn.setDisabled(True)

        self.prev_btn.setDisabled(False)
        self.dynamic_wid.deleteLater()
        new_wid = self.page_list[self.current_page]
        self.dynamic_wid = new_wid()
        self.central_layout.insertWidget(1, self.dynamic_wid)

    def prev_page(self):
        self.current_page -= 1
        if self.current_page < 0:
            self.current_page += 1

        if self.current_page == 0:
            self.prev_btn.setDisabled(True)

        self.next_btn.setDisabled(False)
        self.dynamic_wid.deleteLater()
        new_wid = self.page_list[self.current_page]
        self.dynamic_wid = new_wid()
        self.central_layout.insertWidget(1, self.dynamic_wid)
    
    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
