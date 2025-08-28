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

from ._base_widgets import UListWidgetItem, UMenu, VListWidget
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

    def contextMenuEvent(self, ev):
        self.context_menu = UMenu(ev)

        preview = QAction(Lang.view, self.context_menu)
        preview.triggered.connect(lambda: self.pressed_.emit())
        self.context_menu.addAction(preview)

        self.context_menu.addSeparator()

        show_in_finder = QAction(Lang.reveal_in_finder, self.context_menu)
        show_in_finder.triggered.connect(lambda: self.reveal_cmd())
        self.context_menu.addAction(show_in_finder)

        self.context_menu.show_()
        return super().contextMenuEvent(ev)


class Subwin(VListWidget):
    def __init__(self, path: str):
        super().__init__()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)



        for i in os.scandir(path):
            if i.is_dir():
                item = UListWidgetItem(self, text=i.name)
                self.addItem(item)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)


class CollectionList(VListWidget):
    h_ = 30
    scroll_to_top = pyqtSignal()
    reload_thumbnails = pyqtSignal()
    set_window_title = pyqtSignal()

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
            self.subwin = Subwin(path)
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
            if Dynamic.curr_coll_name == i:
                self.setCurrentRow(self.row(list_item))

    def contextMenuEvent(self, a0):
        a0.ignore()
        return super().contextMenuEvent(a0)


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

    def contextMenuEvent(self, a0):
        menu = UMenu(a0)
        open = QAction(Lang.view, menu)
        open.triggered.connect(lambda: self.cmd("view"))
        menu.addAction(open)
        reveal = QAction(Lang.reveal_in_finder, menu)
        reveal.triggered.connect(lambda: self.cmd("reveal"))
        menu.addAction(reveal)
        menu.show_()


class WinUpload(QTabWidget):
    
    def __init__(self):
        super().__init__()
        self.resize(300, 600)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)
        main_folders = MainFolderList(self)
        main_folders.open_main_folder.connect(lambda index: self.open_main_folder(index))
        self.addTab(main_folders, Lang.folders)
        self.collections_list = CollectionList(0)
        self.addTab(self.collections_list, Lang.collections)

    def open_main_folder(self, index: int):
        self.collections_list.reload(index)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(a0)