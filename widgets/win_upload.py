import os
import re
import subprocess

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QGroupBox, QLabel, QPushButton, QTabWidget

from cfg import JsonData, Static
from system.lang import Lang
from system.main_folder import MainFolder
from system.tasks import LoadCollListTask, LoadDirsTask
from system.utils import UThreadPool

from ._base_widgets import (UHBoxLayout, UListWidgetItem, UMenu, UVBoxLayout,
                            VListWidget, WinChild)


class DirsItem(UListWidgetItem):
    def __init__(self, parent: VListWidget, path: str, height = 30, text = None):
        super().__init__(parent, height, text)
        self.path = path


class DirsList(VListWidget):
    set_path = pyqtSignal(str)

    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self.main_folder_paths = [x for i in MainFolder.list_ for x in  i.paths]
        self.init_ui()

    def init_ui(self):
        self.task_ = LoadDirsTask(self.path)
        self.task_.sigs.finished_.connect(self.init_ui_fin)
        UThreadPool.start(self.task_)
    
    def init_ui_fin(self, dirs: dict[str, str]):        
        self.clear()
        back = DirsItem(parent=self, path=os.path.dirname(self.path), text="...")
        self.addItem(back)

        if self.path in self.main_folder_paths:
            for path, name in sorted(dirs.items(), key=lambda x: self._strip(x[1])):
                item = DirsItem(parent=self, path=path, text=name)
                self.addItem(item)
        else:
            for path, name in dirs.items():
                item = DirsItem(parent=self, path=path, text=name)
                self.addItem(item)
        self.setCurrentRow(0)

    def _strip(self, s: str) -> str:
        return re.sub(r'^[^A-Za-zА-Яа-я]+', '', s)

    def currentItem(self) -> DirsItem:
        return super().currentItem()
        
    def mouseReleaseEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return
        item: DirsItem = self.itemAt(e.pos())
        if item:
            self.path = item.path
            self.init_ui()
            self.set_path.emit(item.path)


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


class InfoBox(QGroupBox):
    def __init__(self):
        super().__init__()
        v_lay = UVBoxLayout()
        v_lay.setSpacing(5)
        v_lay.setContentsMargins(5, 5, 5, 5)

        self.label_bottom = QLabel()
        self.label_bottom.setWordWrap(True)
        self.label_bottom.setAlignment(Qt.AlignmentFlag.AlignTop)
        v_lay.addWidget(self.label_bottom)
        self.setLayout(v_lay)
        self.label_bottom.setFixedHeight(50)

    def set_path(self, path: str):
        self.label_bottom.setText(path)


class WinUpload(WinChild):
    clicked = pyqtSignal(tuple)
    lang = (
        ("Коллекции", "Collections"),
        ("Ок", "Ok"),
        ("Отмена", "Cancel"),
        ("Загрузка", "Upload")
    )

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.lang[3][JsonData.lang])
        self.resize(350, 500)
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)
        self.central_layout.setSpacing(5)
        self.central_layout.setContentsMargins(5, 5, 5, 5)

        self.tab_wid = QTabWidget()
        self.central_layout.addWidget(self.tab_wid)

        self.main_folders = MainFolderList()
        self.main_folders.clicked.connect(self.main_folder_click)
        self.tab_wid.addTab(self.main_folders, Lang.folders)

        self.dirs_list = DirsList(MainFolder.current.curr_path)
        self.tab_wid.addTab(self.dirs_list, self.lang[0][JsonData.lang])

        # новый бокс над кнопками
        self.info_box = InfoBox()
        self.info_box.set_path(MainFolder.current.curr_path)
        self.central_layout.addWidget(self.info_box)
        self.dirs_list.set_path.connect(self.info_box.set_path)

        # кнопки внизу
        btn_lay = UHBoxLayout()
        btn_lay.setSpacing(10)

        self.ok_btn = QPushButton(self.lang[1][JsonData.lang])
        self.ok_btn.clicked.connect(self.ok_cmd)
        self.ok_btn.setFixedWidth(90)

        self.cancel_btn = QPushButton(self.lang[2][JsonData.lang])
        self.cancel_btn.clicked.connect(self.deleteLater)
        self.cancel_btn.setFixedWidth(90)

        btn_lay.addStretch()
        btn_lay.addWidget(self.ok_btn)
        btn_lay.addWidget(self.cancel_btn)
        btn_lay.addStretch()

        self.central_layout.addLayout(btn_lay)

        self.tab_wid.setCurrentIndex(1)

    def main_folder_click(self, main_folder: MainFolder):
        self.dirs_list.path = main_folder.curr_path
        self.dirs_list.init_ui()
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