import os

import sqlalchemy
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QAction, QFileDialog, QMainWindow, QMenu

from cfg import Dynamic, Static
from lang import Lang
from system.main_folder import MainFolder
from signals import SignalsApp
from system.utils import MainUtils, UThreadPool
from system.tasks import FavTask

from .win_info import WinInfo
from .win_warn import WinWarn


class SmbWin:
    @classmethod
    def show(cls, parent_: QMainWindow):
        smb_win = WinWarn(Lang.no_connection, Lang.choose_coll_smb)
        smb_win.adjustSize()
        smb_win.center_relative_parent(parent_)
        smb_win.show()


class OpenInView(QAction):
    _clicked = pyqtSignal()

    def __init__(self, parent_: QMenu):
        super().__init__(parent=parent_, text=Lang.view)
        self.triggered.connect(self._clicked.emit)


class ScanerRestart(QAction):
    def __init__(self, parent: QMenu):
        super().__init__(parent=parent, text=Lang.reload_gui)


class WinInfoAction(QAction):
    def __init__(self, parent: QMenu, win: QMainWindow, rel_img_path_list: list[str]):
        super().__init__(parent=parent, text=Lang.info)
        self.parent_ = parent
        self.win_ = win
        self.rel_img_path_list = rel_img_path_list
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            self.rel_img_path_list = [
                    MainUtils.get_img_path(main_folder_path, i)
                    for i in self.rel_img_path_list
            ]
            self.win = WinInfo(self.rel_img_path_list)
            self.win.finished_.connect(self.open_delayed)
        else:
            self.win = WinWarn(Lang.no_connection, Lang.choose_coll_smb)
            self.win.adjustSize()
            self.win.center_relative_parent(self.win_)
            self.win.show()

    def open_delayed(self):
        self.win.adjustSize()
        self.win.center_relative_parent(self.win_)
        self.win.show()


class CopyPath(QAction):
    def __init__(self, parent: QMenu, win: QMainWindow, rel_img_path_list: list[str]):
        text = f"{Lang.copy_path} ({len(rel_img_path_list)})"
        super().__init__(parent=parent, text=text)
        self.parent_ = parent
        self.win_ = win
        self.rel_img_path_list = rel_img_path_list
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        main_folder_path = MainFolder.current.is_available()

        if main_folder_path:
            img_path_list: list[str] = []
            for i in self.rel_img_path_list:
                i = MainUtils.get_img_path(main_folder_path, i)
                img_path_list.append(i)
            img_path_list = "\n".join(img_path_list)
            MainUtils.copy_text(img_path_list)
        else:
            SmbWin.show(self.win_)


class CopyName(QAction):
    def __init__(self, parent: QMenu, win: QMainWindow, img_path_list: list[str]):
        text = f"{Lang.copy_name} ({len(img_path_list)})"
        super().__init__(parent=parent, text=text)
        self.parent_ = parent
        self.win_ = win
        self.img_path_list = img_path_list
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            names: list[str] = []
            for i in self.img_path_list:
                i = os.path.basename(i)
                i, _ = os.path.splitext(i)
                names.append(i)
            names = "\n".join(names)
            MainUtils.copy_text(names)
        else:
            SmbWin.show(self.win_)


class Reveal(QAction):
    def __init__(self, parent: QMenu, win: QMainWindow, rel_img_path_list: list[str]):
        text = f"{Lang.reveal_in_finder} ({len(rel_img_path_list)})"
        super().__init__(parent=parent, text=text)
        self.rel_img_path_list = rel_img_path_list
        self.parent_ = parent
        self.win_ = win
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            img_path_list = [
                MainUtils.get_img_path(main_folder_path, i)
                for i in self.rel_img_path_list
            ]
            MainUtils.reveal_files(img_path_list)
        else:
            SmbWin.show(self.win_)


class FavActionDb(QAction):
    finished_ = pyqtSignal(int)

    def __init__(self, parent: QMenu, rel_img_path: str, fav_value:  int):

        if fav_value == 0 or fav_value is None:
            t = Lang.add_fav
            self.value = 1

        elif fav_value == 1:
            t = Lang.del_fav
            self.value = 0

        super().__init__(parent=parent, text=t)
        self.triggered.connect(self.cmd_)
        self.rel_img_path = rel_img_path

    def cmd_(self):
        self.task = FavTask(self.rel_img_path, self.value)
        self.task.signals_.finished_.connect(self.finished_.emit)
        UThreadPool.start(self.task)


class Save(QAction):
    save_files = pyqtSignal(tuple)
    def __init__(self, parent: QMenu, win: QMainWindow, rel_img_path_list: list[str], save_as: bool):
        """
        Сигналы:
        - save_files: (папка назначения, список файлов для копирования)
        """
        if save_as:
            text: str = Lang.save_image_in
        else:
            text: str = Lang.save_image_downloads
        text = f"{text} ({len(rel_img_path_list)})"

        super().__init__(parent=parent, text=text)
        self.triggered.connect(self.save_files_cmd)
        self.save_as = save_as
        self.rel_img_path_list = rel_img_path_list
        self.parent_ = parent
        self.win_ = win

    def save_files_cmd(self):
        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            img_path_list = [
                MainUtils.get_img_path(main_folder_path, rel_img_path)
                for rel_img_path in self.rel_img_path_list
            ]
            if self.save_as:
                dialog = QFileDialog()
                dest = dialog.getExistingDirectory()
            else:
                dest = Dynamic.down_folder
            if dest and os.path.isdir(dest):
                self.save_files_finalize(dest, img_path_list)
        else:
            SmbWin.show(self.win_)

    def save_files_finalize(self, dest: str, img_path_list: list):
        data = (dest, img_path_list)
        self.save_files.emit(data)


class MenuTypes(QMenu):
    reload_thumbnails = pyqtSignal()
    update_bottom_bar = pyqtSignal()

    def __init__(self, parent: QMenu):
        """
        Сигналы:
        - reload_thumbnails()
        - update_bottom_bar()
        """
        super().__init__(parent=parent, title=Lang.type_show)

        type_jpg = QAction(parent=self, text=Lang.type_jpg)
        type_jpg.setCheckable(True)
        cmd_jpg = lambda: self.cmd_(action_=type_jpg, type_=Static.ext_non_layers)
        type_jpg.triggered.connect(cmd_jpg)
        self.addAction(type_jpg)

        type_tiff = QAction(parent=self, text=Lang.type_tiff)
        type_tiff.setCheckable(True)
        cmd_tiff = lambda: self.cmd_(action_=type_tiff, type_=Static.ext_layers)
        type_tiff.triggered.connect(cmd_tiff)
        self.addAction(type_tiff)

        if Static.ext_non_layers in Dynamic.types:
            type_jpg.setChecked(True)

        if Static.ext_layers in Dynamic.types:
            type_tiff.setChecked(True)

    def cmd_(self, action_: QAction, type_: str):

        if type_ in Dynamic.types:
            Dynamic.types.remove(type_)
            action_.setChecked(False)

        else:
            Dynamic.types.append(type_)
            action_.setChecked(True)
        self.reload_thumbnails.emit()
        self.update_bottom_bar.emit()


class RemoveFiles(QAction):
    def __init__(self, parent: QMenu, total: int):
        text_ = f"{Lang.delete} ({total})"
        super().__init__(text_, parent)


class MoveFiles(QAction):
    def __init__(self, parent: QMenu, rel_img_path_list: list[str]):
        text = f"{Lang.move_files} ({len(rel_img_path_list)})"
        super().__init__(text=text, parent=parent)
