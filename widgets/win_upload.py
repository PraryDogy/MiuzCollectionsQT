import os
import re
from typing import Dict

from PyQt5.QtCore import QObject, QSize, Qt, QThreadPool, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QGroupBox, QLabel, QPushButton,
                             QTabWidget, QTreeWidget, QTreeWidgetItem, QWidget)

from cfg import Cfg
from system.lang import Lng
from system.main_folder import MainFolder
from system.tasks import LoadDirsTask
from system.utils import UThreadPool

from ._base_widgets import (UHBoxLayout, UListWidgetItem, UVBoxLayout,
                            VListWidget, WinChild)


class MyTree(QTreeWidget):
    clicked_: pyqtSignal = pyqtSignal(str)
    hh = 25

    def __init__(self, root_dir: str) -> None:
        super().__init__()
        # root_dir = "/Users"
        self.root_dir = root_dir
        self.setHeaderHidden(True)
        self.itemClicked.connect(self.on_item_click)
        self.first_load()

    def first_load(self):
        self.clear()
        root_item: QTreeWidgetItem = QTreeWidgetItem([os.path.basename(self.root_dir)])
        root_item.setSizeHint(0, QSize(0, self.hh))
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.root_dir)  # полный путь
        self.addTopLevelItem(root_item)

        worker: LoadDirsTask = LoadDirsTask(self.root_dir)
        worker.sigs.finished_.connect(lambda data, item=root_item: self.add_children(item, data))
        worker.sigs.finished_.connect(self.clearFocus)
        UThreadPool.start(worker)

    def on_item_click(self, item: QTreeWidgetItem, col: int) -> None:
        path: str = item.data(0, Qt.ItemDataRole.UserRole)
        self.clicked_.emit(path)
        if item.childCount() == 0:
            worker: LoadDirsTask = LoadDirsTask(path)
            worker.sigs.finished_.connect(lambda data, item=item: self.add_children(item, data))
            UThreadPool.start(worker)
        item.setExpanded(True)

    def add_children(self, parent_item: QTreeWidgetItem, data: Dict[str, str]) -> None:
        parent_item.takeChildren()  # удаляем заглушку
        for path, name in data.items():
            child: QTreeWidgetItem = QTreeWidgetItem([name])
            child.setSizeHint(0, QSize(0, self.hh))
            child.setData(0, Qt.ItemDataRole.UserRole, path)  # полный путь
            parent_item.addChild(child)


# ПЕРВАЯ ВКАДКА ПЕРВАЯ ВКАДКА  ПЕРВАЯ ВКАДКА  ПЕРВАЯ ВКАДКА  ПЕРВАЯ ВКАДКА  ПЕРВАЯ ВКАДКА 


class MainFolderItem(UListWidgetItem):
    def __init__(self, parent: VListWidget, main_folder: MainFolder, height = 30, text = None):
        super().__init__(parent, height, text)
        self.main_folder = main_folder


class MainFolderList(VListWidget):
    clicked = pyqtSignal(MainFolder)

    def __init__(self):
        super().__init__()
        for i in MainFolder.list_:
            item = MainFolderItem(parent=self, main_folder=i, text=i.name)
            self.addItem(item)
        self.setCurrentRow(0)

    def currentItem(self) -> MainFolderItem:
        return super().currentItem()

    def mouseReleaseEvent(self, e):
        item = self.currentItem()
        if e.button() == Qt.MouseButton.LeftButton and item:
            path = item.main_folder.availability()
            if path:
                self.clicked.emit(item.main_folder)
        return super().mouseReleaseEvent(e)


# ОСНОВНОЕ ОКНО ОСНОВНОЕ ОКНО ОСНОВНОЕ ОКНО ОСНОВНОЕ ОКНО ОСНОВНОЕ ОКНО ОСНОВНОЕ ОКНО 


class PathWindow(WinChild):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lng.upload_path[Cfg.lng])
        self.central_layout.setContentsMargins(5, 5, 5, 5)
        self.text_label = QLabel()
        self.text_label.setWordWrap(True)
        self.central_layout.addWidget(self.text_label)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)


class PathWidget(QGroupBox):
    def __init__(self):
        super().__init__()
        v_lay = UVBoxLayout()
        v_lay.setSpacing(5)
        v_lay.setContentsMargins(5, 5, 5, 5)

        self.label_bottom = QLabel()
        self.label_bottom.mouseReleaseEvent = self.show_path_win
        self.label_bottom.setAlignment(Qt.AlignmentFlag.AlignTop)
        v_lay.addWidget(self.label_bottom)
        self.setLayout(v_lay)

    def set_path(self, path: str):
        self.label_bottom.setText(path)

    def show_path_win(self, *args):
        self.win = PathWindow()
        self.win.text_label.setText(self.label_bottom.text())
        self.win.setMinimumSize(400, 30)
        self.win.setMaximumWidth(900)
        self.win.adjustSize()
        self.win.center_relative_parent(self.window())
        self.win.show()


class WinUpload(WinChild):
    clicked = pyqtSignal(tuple)
 
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Lng.upload[Cfg.lng])
        self.setFixedSize(650, 500)
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)
        self.central_layout.setSpacing(5)
        self.central_layout.setContentsMargins(5, 10, 5, 5)

        self.tab_wid = QTabWidget()
        self.central_layout.addWidget(self.tab_wid)

        self.main_folders = MainFolderList()
        self.main_folders.clicked.connect(self.main_folder_click)
        self.tab_wid.addTab(self.main_folders, Lng.folders[Cfg.lng])

        self.dirs_list = MyTree(MainFolder.current.curr_path)
        self.tab_wid.addTab(self.dirs_list, Lng.collections[Cfg.lng])

        # новый бокс над кнопками
        self.info_box = PathWidget()
        self.info_box.setMaximumWidth(self.width())
        self.info_box.set_path(MainFolder.current.curr_path)
        self.central_layout.addWidget(self.info_box)
        self.dirs_list.clicked_.connect(self.info_box.set_path)

        # кнопки внизу
        btn_lay = UHBoxLayout()
        btn_lay.setSpacing(10)

        self.ok_btn = QPushButton(Lng.ok[Cfg.lng])
        self.ok_btn.clicked.connect(self.ok_cmd)
        self.ok_btn.setFixedWidth(90)

        self.cancel_btn = QPushButton(Lng.cancel[Cfg.lng])
        self.cancel_btn.clicked.connect(self.deleteLater)
        self.cancel_btn.setFixedWidth(90)

        btn_lay.addStretch()
        btn_lay.addWidget(self.ok_btn)
        btn_lay.addWidget(self.cancel_btn)
        btn_lay.addStretch()

        self.central_layout.addLayout(btn_lay)

        self.tab_wid.setCurrentIndex(1)

    def main_folder_click(self, main_folder: MainFolder):
        self.dirs_list.root_dir = main_folder.curr_path
        self.dirs_list.first_load()
        self.info_box.set_path(main_folder.curr_path)
        self.tab_wid.setCurrentIndex(1)

    def ok_cmd(self):
        path = self.info_box.label_bottom.text()
        if path:
            data = (self.main_folders.currentItem().main_folder, path)
            self.clicked.emit(data)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)