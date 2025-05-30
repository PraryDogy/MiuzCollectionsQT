import os

import sqlalchemy
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QAction, QFileDialog, QMainWindow, QMenu

from cfg import Dynamic, Static
from database import THUMBS, Dbase
from lang import Lang
from main_folders import MainFolder
from signals import SignalsApp
from utils.copy_files import CopyFiles
from utils.scaner import Scaner
from utils.utils import Utils

from ._runnable import URunnable, UThreadPool
from .win_info import WinInfo
from .win_smb import WinSmb


class OpenWins:

    @classmethod
    def info_db(cls, parent_: QMainWindow, short_src: str, coll_folder: str):

        if not isinstance(parent_, QMainWindow):
            raise TypeError

        WinInfo(
            parent=parent_,
            short_src=short_src,
            coll_folder=coll_folder
        )

    @classmethod
    def smb(cls, parent_: QMainWindow):

        if not isinstance(parent_, QMainWindow):
            raise TypeError

        smb_win = WinSmb()
        smb_win.center_relative_parent(parent_)
        smb_win.show()

    @classmethod
    def dialog_dirs(cls):
        dialog = QFileDialog()
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        return dialog


class OpenInView(QAction):
    _clicked = pyqtSignal()

    def __init__(self, parent_: QMenu):
        super().__init__(parent=parent_, text=Lang.view)
        self.triggered.connect(self._clicked.emit)


class ScanerRestart(QAction):
    def __init__(self, parent: QMenu):
        super().__init__(parent=parent, text=Lang.reload_gui)
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        SignalsApp.instance.progressbar_text.emit(Lang.preparing.capitalize())
        Scaner.stop()
        QTimer.singleShot(5000, Scaner.start)


class OpenInfoDb(QAction):
    def __init__(self, parent: QMenu, win: QMainWindow, short_src: str):
        super().__init__(parent=parent, text=Lang.info)
        self.parent_ = parent
        self.win_ = win
        self.short_src = short_src
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        MainFolder.current.set_current_path()
        coll_folder = MainFolder.current.get_current_path()
        
        if coll_folder:
            OpenWins.info_db(
                parent_=self.win_,
                short_src=self.short_src,
                coll_folder=coll_folder    
            )
        else:
            OpenWins.smb(parent_=self.win_)


class CopyPath(QAction):
    def __init__(self, parent: QMenu, win: QMainWindow, short_src: str):
        super().__init__(parent=parent, text=Lang.copy_path)
        self.parent_ = parent
        self.win_ = win
        self.short_src = short_src
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        MainFolder.current.set_current_path()
        coll_folder = MainFolder.current.get_current_path()

        if coll_folder:
            full_src = Utils.get_full_src(coll_folder, self.short_src)
            Utils.copy_text(text=full_src)
        else:
            OpenWins.smb(parent_=self.win_)


class CopyName(QAction):
    def __init__(self, parent: QMenu, win: QMainWindow, short_src: str):
        super().__init__(parent=parent, text=Lang.copy_name)
        self.parent_ = parent
        self.win_ = win
        self.short_src = short_src
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        MainFolder.current.set_current_path()
        coll_folder = MainFolder.current.get_current_path()

        if coll_folder:
            name = os.path.basename(self.short_src)
            name, _ = os.path.splitext(name)
            Utils.copy_text(name)
        else:
            OpenWins.smb(parent_=self.win_)


class Reveal(QAction):
    def __init__(self, parent: QMenu, win: QMainWindow, short_src: str | list):

        if isinstance(short_src, list):
            text = f"{Lang.reveal_in_finder} ({len(short_src)})"
        else:
            text = f"{Lang.reveal_in_finder} (1)"
            short_src = [short_src]

        super().__init__(parent=parent, text=text)
        self.short_src = short_src
        self.parent_ = parent
        self.win_ = win
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        MainFolder.current.set_current_path()
        coll_folder = MainFolder.current.get_current_path()
        if coll_folder:
            full_src = [
                Utils.get_full_src(coll_folder, i)
                for i in self.short_src
            ]
            Utils.reveal_files(files_list=full_src)
        else:
            OpenWins.smb(parent_=self.win_)


class WorkerSignals(QObject):
    finished_ = pyqtSignal(int)


class FavTask(URunnable):
    def __init__(self, short_src: str, value: int):
        super().__init__()
        self.signals_ = WorkerSignals()
        self.short_src = short_src
        self.value = value

    def task(self):
        values = {"fav": self.value}
        q = sqlalchemy.update(THUMBS).where(THUMBS.c.short_src==self.short_src)
        q = q.values(**values)

        conn = Dbase.engine.connect()

        try:
            conn.execute(q)
            conn.commit()
            self.signals_.finished_.emit(self.value)
        except Exception as e:
            Utils.print_error(e)
            conn.rollback()

        conn.close()


class FavActionDb(QAction):
    finished_ = pyqtSignal(int)

    def __init__(self, parent: QMenu, short_src: str, fav_value:  int):

        if fav_value == 0 or fav_value is None:
            t = Lang.add_fav
            self.value = 1

        elif fav_value == 1:
            t = Lang.del_fav
            self.value = 0

        super().__init__(parent=parent, text=t)
        self.triggered.connect(self.cmd_)
        self.short_src = short_src

    def cmd_(self):
        self.task = FavTask(short_src=self.short_src, value=self.value)
        self.task.signals_.finished_.connect(self.finished_.emit)
        UThreadPool.start(self.task)


class Save(QAction):
    def __init__(self, parent: QMenu, win: QMainWindow, short_src: str | list, save_as: bool):

        if save_as:
            text: str = Lang.save_image_in
        else:
            text: str = Lang.save_image_downloads

        if isinstance(short_src, list):
            text = f"{text} ({len(short_src)})"
        else:
            text = f"{text} (1)"
            short_src = [short_src]

        super().__init__(parent=parent, text=text)
        self.triggered.connect(self.cmd_)
        self.save_as = save_as
        self.short_src: list = short_src
        self.parent_ = parent
        self.win_ = win

    def cmd_(self):
        MainFolder.current.set_current_path()
        coll_folder = MainFolder.current.get_current_path()

        if coll_folder:

            full_src = [
                Utils.get_full_src(coll_folder, url)
                for url in self.short_src
            ]

            if self.save_as:
                dialog = OpenWins.dialog_dirs()
                dest = dialog.getExistingDirectory()

            else:
                dest = Dynamic.down_folder

            if dest:
                self.copy_files_cmd(dest=dest, full_src=full_src)
        else:
            OpenWins.smb(parent_=self.win_)

    def copy_files_cmd(self, dest: str, full_src: str | list):
        thread_ = CopyFiles(dest, full_src)
        UThreadPool.start(thread_)


class MenuTypes(QMenu):
    def __init__(self, parent: QMenu):
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

        SignalsApp.instance.grid_thumbnails_cmd.emit("reload")
        SignalsApp.instance.bar_bottom_filters.emit()


class RemoveFiles(QAction):
    def __init__(self, parent: QMenu, total: int):
        text_ = f"{Lang.delete} ({total})"
        super().__init__(text_, parent)