import os

import sqlalchemy
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QAction, QFileDialog, QMainWindow, QWidget

from cfg import Dynamic, JsonData
from database import THUMBS, Dbase
from signals import SignalsApp
from utils.copy_files import ThreadCopyFiles
from utils.scaner import Scaner
from utils.utils import URunnable, UThreadPool, Utils

from .win_info import WinInfo
from .win_smb import WinSmb


class Shared:
    dialog: QFileDialog | None = None

    @classmethod
    def show_smb(cls, parent_: QWidget | QMainWindow):

        if not isinstance(parent_, QMainWindow):
            parent_ = parent_.window()

        smb_win = WinSmb()
        smb_win.center_relative_parent(parent_)
        smb_win.show()


class OpenWins:

    @classmethod
    def info(cls, parent: QWidget, src: str):
        WinInfo(parent, src)


class CustomAction(QAction):
    def __init__(self, parent: QWidget, src: str, text: str):
        super().__init__(text=text)

        self.src = src
        self.parent_ = parent

    def cmd(self, *args, **kwargs):
        print("context img > custom action > empty cmd")


class OpenInView(CustomAction):
    def __init__(self, parent: QWidget, src: str):
        super().__init__(parent, src, Dynamic.lng.view)
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        SignalsApp.all_.win_img_view_open_in.emit(self.parent_)


class ReloadGui(CustomAction):
    def __init__(self, parent: QWidget, src: str):
        super().__init__(parent, src, Dynamic.lng.reload_gui)
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        Scaner.stop()
        Scaner.start()


class OpenInfo(CustomAction):
    def __init__(self, parent: QWidget, src: str):
        super().__init__(parent, src, Dynamic.lng.info)
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        if Utils.smb_check():
            OpenWins.info(self.parent_, self.src)
        else:
            Shared.show_smb(self.parent_)


class CopyPath(CustomAction):
    def __init__(self, parent: QWidget, src: str):
        super().__init__(parent, src, Dynamic.lng.copy_path)
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        if Utils.smb_check():
            Utils.copy_text(text=self.src)
        else:
            Shared.show_smb(self.parent_)

class Reveal(CustomAction):
    def __init__(self, parent: QWidget, src: str):
        super().__init__(parent, src, Dynamic.lng.reveal_in_finder)
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        if Utils.smb_check():
            Utils.reveal_files([self.src])
        else:
            Shared.show_smb(self.parent_)


class WorkerSignals(QObject):
    finished_ = pyqtSignal(int)


class FavTask(URunnable):
    def __init__(self, src: str, value: int):
        super().__init__()
        self.signals_ = WorkerSignals()
        self.src = src.replace(JsonData.coll_folder, "")
        self.value = value

    @URunnable.set_running_state
    def run(self):
        values = {"fav": self.value}
        q = sqlalchemy.update(THUMBS).where(THUMBS.c.src==self.src)
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


class FavAction(CustomAction):
    finished_ = pyqtSignal(int)

    def __init__(self, parent: QWidget, src: str, fav:  int):

        if fav == 0:
            t = Dynamic.lng.add_fav
            self.value = 1

        elif fav == 1 or fav is None:
            t = Dynamic.lng.del_fav
            self.value = 0

        super().__init__(parent, src, t)
        self.triggered.connect(self.cmd_)

    def cmd_(self):
        self.task = FavTask(self.src, self.value)
        self.task.signals_.finished_.connect(self.finished_.emit)
        UThreadPool.pool.start(self.task)


class Save(CustomAction):
    def __init__(self, parent: QWidget, src: str, save_as: bool):

        if save_as:
            text: str = Dynamic.lng.save_image_in
        else:
            text: str = Dynamic.lng.save_image_downloads

        super().__init__(parent, src, text)
        self.triggered.connect(self.cmd_)
        self.save_as = save_as

    def cmd_(self):
        if Utils.smb_check():
            if self.save_as:
                Shared.dialog = QFileDialog()
                Shared.dialog.setOption(QFileDialog.ShowDirsOnly, True)
                dest = Shared.dialog.getExistingDirectory()
            else:
                dest = JsonData.down_folder

            if dest:
                self.copy_files_cmd(dest=dest, file=self.src)
        else:
            Shared.show_smb(self.parent_)

    def copy_files_cmd(self, dest: str, file: str | list):

        if not file or not os.path.exists(file):
            return

        if isinstance(file, str):
            file = [file]

        cmd_ = lambda f: self.reveal_copied_files(files=f)
        thread_ = ThreadCopyFiles(dest=dest, files=file)
        thread_.signals_.finished_.connect(cmd_)

        SignalsApp.all_.btn_downloads_toggle.emit("show")
        UThreadPool.pool.start(thread_)

    def reveal_copied_files(self, files: list):

        Utils.reveal_files(files)

        if len(Dynamic.copy_threads) == 0:
            SignalsApp.all_.btn_downloads_toggle.emit("hide")
