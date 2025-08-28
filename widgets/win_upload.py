import os
import re
import subprocess

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QAction, QLabel, QTabWidget

from cfg import Dynamic, JsonData, Static
from system.lang import Lang
from system.main_folder import MainFolder
from system.tasks import LoadCollListTask
from system.utils import UThreadPool

from ._base_widgets import UListWidgetItem, UMenu, VListWidget, WinChild
from .win_warn import WinWarn


class BaseCollBtn(QLabel):
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


class CollBtn(BaseCollBtn):
    def __init__(self, text: str):
        super().__init__(text)

    def reveal_cmd(self, *args) -> None:
        main_folder_path = MainFolder.current.availability()
        if main_folder_path:
            if self.coll_name in (Static.NAME_ALL_COLLS, Static.NAME_FAVS, Static.NAME_RECENTS):
                coll = main_folder_path
            else:
                coll = os.path.join(main_folder_path, self.coll_name)
            subprocess.Popen(["open", coll])
        else:
            self.win_warn = WinWarn(Lang.no_connection, Lang.no_connection_descr)
            self.win_warn.adjustSize()
            self.win_warn.center_relative_parent(self.window())
            self.win_warn.show()

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.pressed_.emit()


class _SubWin(VListWidget):
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
            print(path)

        return super().mouseReleaseEvent(e)
    

class SubWin(WinChild):
    clicked = pyqtSignal(str)

    def __init__(self, path):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)
        self.v_list = _SubWin(path)
        self.v_list.clicked.connect(self.clicked.emit)
        self.central_layout.addWidget(self.v_list)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)
    

class CollectionList(VListWidget):
    h_ = 30
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
        if os.path.exists(path):
            self.subwin = SubWin(path)
            self.subwin.clicked.connect(self.clicked.emit)
            self.subwin.adjustSize()
            self.subwin.show()

    def init_ui(self, menus: list[str]):
        self.clear()
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

    def __init__(self, parent: QTabWidget):
        super().__init__(parent=parent)
        for i in MainFolder.list_:
            item = UListWidgetItem(parent=self, text=i.name)
            self.addItem(item)
        self.setCurrentRow(0)

    def cmd(self, flag: str):
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

        if flag == "reveal":
            subprocess.Popen(["open", path])
        elif flag == "view":
            index = MainFolder.list_.index(folder)
            self.open_main_folder.emit(index)

    def mouseReleaseEvent(self, e):
        idx = self.indexAt(e.pos())
        if not idx.isValid():
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self.cmd("view")
        return super().mouseReleaseEvent(e)


class WinUpload(WinChild):
    clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.resize(300, 500)
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)
        self.tab_wid = QTabWidget()
        self.central_layout.addWidget(self.tab_wid)

        main_folders = MainFolderList(self.tab_wid)
        main_folders.open_main_folder.connect(lambda index: self.open_main_folder(index))
        self.tab_wid.addTab(main_folders, Lang.folders)
        self.collections_list = CollectionList(0)
        self.collections_list.clicked.connect(self.clicked.emit)
        self.tab_wid.addTab(self.collections_list, Lang.collections)

    def open_main_folder(self, index: int):
        self.collections_list.reload(index)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)