import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QLabel, QPushButton, QTreeWidget, QTreeWidgetItem,
                             QWidget)

from cfg import Cfg, Static
from system.lang import Lng

from ._base_widgets import UHBoxLayout, UVBoxLayout, WinSystem


class BasePage(QTreeWidget):
    clicked_= pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.setDisabled(True)


class PageOne(BasePage):
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
        

class PageTwo(BasePage):
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)

        # Корневая папка
        folder_item = QTreeWidgetItem(self, [Lng.collection_folder[Cfg.lng]])

        # Добавляем изображения напрямую в папку
        for i in range(1, 11):  # четыре изображения
            QTreeWidgetItem(folder_item, [f"{Lng.image[Cfg.lng]} {i}"])

        self.expandAll()


class PageThree(BasePage):
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
        self.central_layout.setContentsMargins(10, 5, 10, 10)
        self.central_layout.setSpacing(15)

        descr = QLabel(Lng.help_text[Cfg.lng])
        self.central_layout.insertWidget(0, descr)

        self.current_page = 0
        self.max_pages = 2
        self.page_list = [
            lambda: self.create_page(PageOne, 0),
            lambda: self.create_page(PageTwo, 1),
            lambda: self.create_page(PageThree, 2)
        ]

        self.dynamic_wid = self.page_list[0]()
        self.central_layout.insertWidget(1, self.dynamic_wid)
        self.setFixedSize(450, 420)

    def create_page(self, wid: QTreeWidget, page_num: int):
        tree: QTreeWidget = wid()
        tree.clicked.connect(self.next_page)
        return tree
    
    def next_page(self):
        self.current_page += 1
        if self.current_page > self.max_pages:
            self.current_page = 0

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
