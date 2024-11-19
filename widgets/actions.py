import os

import sqlalchemy
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QAction, QFileDialog, QMainWindow, QMenu, QWidget

from cfg import JsonData
from database import THUMBS, Dbase
from lng import Lng
from signals import SignalsApp
from utils.copy_files import CopyFiles
from utils.scaner import Scaner
from utils.utils import URunnable, UThreadPool, Utils

from .win_info import WinInfo
from .win_smb import WinSmb


class OpenWins:

    @classmethod
    def info_db(cls, parent_: QMainWindow, short_src: str):

        if not isinstance(parent_, QMainWindow):
            raise TypeError

        WinInfo(parent=parent_, short_src=short_src)

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
        super().__init__(parent=parent_, text=Lng.view)
        self.triggered.connect(self._clicked.emit)


class ScanerRestart(QAction):
    def __init__(self, parent: QMenu):
        super().__init__(parent=parent, text=Lng.reload_gui)
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        Scaner.stop()
        Scaner.start()


class OpenInfoDb(QAction):
    def __init__(self, parent: QMenu, win: QMainWindow, short_src: str):
        super().__init__(parent=parent, text=Lng.info)
        self.parent_ = parent
        self.win_ = win
        self.short_src = short_src
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        if Utils.smb_check():
            OpenWins.info_db(parent_=self.win_, short_src=self.short_src)
        else:
            OpenWins.smb(parent_=self.win_)


class CopyPath(QAction):
    def __init__(self, parent: QMenu, win: QMainWindow, full_src: str):
        super().__init__(parent=parent, text=Lng.copy_path)
        self.parent_ = parent
        self.win_ = win
        self.full_src = full_src
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        if Utils.smb_check():
            Utils.copy_text(text=self.full_src)
        else:
            OpenWins.smb(parent_=self.win_)


class Reveal(QAction):
    def __init__(self, parent: QMenu, win: QMainWindow, full_src: str):
        super().__init__(parent=parent, text=Lng.reveal_in_finder)
        self.full_src = full_src
        self.parent_ = parent
        self.win_ = win
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        if Utils.smb_check():
            Utils.reveal_files([self.full_src])
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

    @URunnable.set_running_state
    def run(self):
        values = {"fav": self.value}
        q = sqlalchemy.update(THUMBS).where(THUMBS.c.src==self.short_src)
        q = q.values(**values)

        conn = Dbase.engine.connect()

        try:
            conn.execute(q)
            conn.commit()
            self.signals_.finished_.emit(self.value)
        except Exception as e:
            Utils.print_err(error=e)
            conn.rollback()

        conn.close()


class FavActionDb(QAction):
    finished_ = pyqtSignal(int)

    def __init__(self, parent: QMenu, short_src: str, fav_value:  int):

        if fav_value == 0 or fav_value is None:
            t = Lng.add_fav
            self.value = 1

        elif fav_value == 1:
            t = Lng.del_fav
            self.value = 0

        super().__init__(parent=parent, text=t)
        self.triggered.connect(self.cmd_)
        self.short_src = short_src

    def cmd_(self):
        self.task = FavTask(short_src=self.short_src, value=self.value)
        self.task.signals_.finished_.connect(self.finished_.emit)
        UThreadPool.pool.start(self.task)


class Save(QAction):
    def __init__(self, parent: QMenu, win: QMainWindow, full_src: str, save_as: bool):

        if save_as:
            text: str = Lng.save_image_in
        else:
            text: str = Lng.save_image_downloads

        super().__init__(parent=parent, text=text)
        self.triggered.connect(self.cmd_)
        self.save_as = save_as
        self.full_src = full_src
        self.parent_ = parent
        self.win_ = win

    def cmd_(self):
        if Utils.smb_check():
            if self.save_as:
                dialog = OpenWins.dialog_dirs()
                dest = dialog.getExistingDirectory()
            else:
                dest = JsonData.down_folder

            if dest:
                self.copy_files_cmd(dest=dest, full_src=self.full_src)
        else:
            OpenWins.smb(parent_=self.win_)

    def copy_files_cmd(self, dest: str, full_src: str | list):

        if not full_src or not os.path.exists(full_src):
            return

        if isinstance(full_src, str):
            full_src = [full_src]

        cmd_ = lambda f: self.reveal_copied_files(files=f)
        thread_ = CopyFiles(dest=dest, files=full_src)
        thread_.signals_.finished_.connect(cmd_)

        SignalsApp.all_.btn_downloads_toggle.emit("show")
        UThreadPool.pool.start(thread_)

    def reveal_copied_files(self, files: list):

        Utils.reveal_files(files)

        if len(CopyFiles.current_threads) == 0:
            SignalsApp.all_.btn_downloads_toggle.emit("hide")
