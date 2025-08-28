import os
import re
import subprocess

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QAction, QLabel, QTabWidget

from cfg import JsonData, Static
from system.lang import Lang
from system.main_folder import MainFolder
from system.tasks import LoadCollListTask
from system.utils import UThreadPool

from ._base_widgets import UListWidgetItem, UMenu, VListWidget, WinChild
from .win_warn import WinWarn


class SubWinList(VListWidget):
    clicked = pyqtSignal(str)

    def __init__(self, path: str):
        super().__init__()
        root = UListWidgetItem(self, text=os.path.basename(path))
        root.path = path
        self.addItem(root)
        for i in os.scandir(path):
            if i.is_dir():
                item = UListWidgetItem(self, text=i.name)
                item.path = i.path
                self.addItem(item)
        self.setCurrentRow(0)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            path = self.currentItem().path
            self.clicked.emit(path)
        return super().mouseReleaseEvent(e)
    

class SubWin(WinChild):
    clicked = pyqtSignal(str)

    def __init__(self, path):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)
        self.v_list = SubWinList(path)
        self.v_list.clicked.connect(self.clicked.emit)
        self.central_layout.addWidget(self.v_list)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)


class CollBtn(QLabel):
    pressed_ = pyqtSignal()

    def __init__(self, text: str):
        self.coll_name = text
        data = {
            Static.NAME_ALL_COLLS: Lang.all_colls,
            Static.NAME_RECENTS: Lang.recents,
            Static.NAME_FAVS: Lang.fav_coll
        }
        if text in data:
            text = data.get(text)
        if JsonData.abc_name:
            text = re.sub(r'^[^A-Za-zА-Яа-я]+', '', text)
        super().__init__(text=text)
        self.setStyleSheet("padding-left: 5px;")

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.pressed_.emit()


class CollBtnList(VListWidget):
    clicked = pyqtSignal(str)

    def __init__(self, main_folder_index: int):
        super().__init__()
        self.main_folder_index = main_folder_index
        self.load_coll_list()

    def reload(self, main_folder_index: int):
        self.main_folder_index = main_folder_index
        self.load_coll_list()

    def load_coll_list(self):
        main_folder = MainFolder.list_[self.main_folder_index]
        self.task_ = LoadCollListTask(main_folder)
        self.task_.signals_.finished_.connect(self.init_ui)
        UThreadPool.start(self.task_)

    def collection_btn_cmd(self, btn: CollBtn):
        main_folder = MainFolder.list_[self.main_folder_index]
        path = os.path.join(main_folder.curr_path, btn.coll_name)
        if btn.coll_name == Static.NAME_ALL_COLLS:
            path = main_folder.curr_path
            self.clicked.emit(path)
        elif os.path.exists(path):
            self.subwin = SubWin(path)
            self.subwin.clicked.connect(self.clicked.emit)
            self.subwin.adjustSize()
            self.subwin.center_relative_parent(self.window())
            self.subwin.show()

    def init_ui(self, menus: list[str]):
        self.clear()

        coll_btn = CollBtn(Static.NAME_ALL_COLLS)
        cmd_ = lambda wid=coll_btn: self.collection_btn_cmd(wid)
        coll_btn.pressed_.connect(cmd_)
        list_item = UListWidgetItem(self)
        self.addItem(list_item)
        self.setItemWidget(list_item, coll_btn)

        for i in menus:
            coll_btn = CollBtn(i)
            cmd_ = lambda wid=coll_btn: self.collection_btn_cmd(wid)
            coll_btn.pressed_.connect(cmd_)
            list_item = UListWidgetItem(self)
            self.addItem(list_item)
            self.setItemWidget(list_item, coll_btn)
        self.setCurrentRow(0)


class MainFolderList(VListWidget):
    open_main_folder = pyqtSignal(int)
    double_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        for i in MainFolder.list_:
            item = UListWidgetItem(parent=self, text=i.name)
            self.addItem(item)
        self.setCurrentRow(0)

    def view(self):
        name = self.currentItem().text()
        folder = next((i for i in MainFolder.list_ if i.name == name), None)
        if folder is None:
            return
        path = folder.availability()
        if not path:
            self.win_warn = WinWarn(Lang.no_connection, Lang.no_connection_descr)
            self.win_warn.center_relative_parent(self.window())
            self.win_warn.show()
            return
        index = MainFolder.list_.index(folder)
        self.open_main_folder.emit(index)

    def mouseDoubleClickEvent(self, e):
        idx = self.indexAt(e.pos())
        if not idx.isValid():
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        return super().mouseDoubleClickEvent(e)

    def mouseReleaseEvent(self, e):
        idx = self.indexAt(e.pos())
        if not idx.isValid():
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self.view()
        return super().mouseReleaseEvent(e)


class WinUpload(WinChild):
    clicked = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self.resize(250, 500)
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)
        self.tab_wid = QTabWidget()
        self.central_layout.addWidget(self.tab_wid)

        self.main_folders = MainFolderList()
        self.main_folders.open_main_folder.connect(lambda index: self.collections_list.reload(index))
        self.main_folders.double_clicked.connect(lambda: self.tab_wid.setCurrentIndex(1))
        self.tab_wid.addTab(self.main_folders, Lang.folders)
        self.collections_list = CollBtnList(0)
        self.collections_list.clicked.connect(self.clicked_cmd)
        self.tab_wid.addTab(self.collections_list, Lang.collections)

        self.tab_wid.setCurrentIndex(1)

    def clicked_cmd(self, path: str):
        data = (path, self.main_folders.currentItem().text())
        self.clicked.emit(data)
        if hasattr(self.collections_list, "subwin"):
            self.collections_list.subwin.deleteLater()
        self.deleteLater()

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)