import os

from PyQt5.QtWidgets import QAction, QFileDialog, QMainWindow, QWidget

from base_widgets import ContextCustom
from cfg import Dynamic, JsonData
from signals import SignalsApp
from utils.copy_files import ThreadCopyFiles
from utils.main_utils import MainUtils

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
        SignalsApp.all.win_img_view_open_in.emit(self.parent_)


class OpenInfo(CustomAction):
    def __init__(self, parent: QWidget, src: str):
        super().__init__(parent, src, Dynamic.lng.info)
        self.triggered.connect(self.cmd)

    def cmd(self, *args):
        if MainUtils.smb_check():
            self.win_info = WinInfo(src=self.src)
            self.win_info.center_relative_parent(self.parent_)
            self.win_info.show()
        else:
            Shared.show_smb(self.parent_)


class CopyPath(CustomAction):
    def __init__(self, parent: QWidget, src: str):
        super().__init__(parent, src, Dynamic.lng.copy_path)
        cmd_ = lambda: MainUtils.copy_text(text=self.src)
        self.triggered.connect(cmd_)


class Reveal(CustomAction):
    def __init__(self, parent: QWidget, src: str):
        super().__init__(parent, src, Dynamic.lng.reveal_in_finder)
        cmd_ = lambda: MainUtils.reveal_files([self.src])
        self.triggered.connect(cmd_)


class Save(CustomAction):
    def __init__(self, parent: QWidget, src: str, save_as: bool):

        if save_as:
            text: str = Dynamic.lng.save_image_in
        else:
            text: str = Dynamic.lng.save_image_downloads

        super().__init__(parent, src, text)
        self.triggered.connect(self.cmd)
        self.save_as = save_as

    def cmd(self):
        if MainUtils.smb_check():
            if self.save_as:
                Shared.dialog = QFileDialog()
                Shared.dialog.setOption(QFileDialog.ShowDirsOnly, True)
                dest = Shared.dialog.getExistingDirectory()
            else:
                dest = JsonData.down_folder

            if dest:
                self.copy_files_cmd(dest=dest, file=self.src)
        else:
            Shared.show_smb()

    def copy_files_cmd(self, dest: str, file: str | list):

        if not file or not os.path.exists(file):
            MainUtils.send_notification(Dynamic.lng.no_file)
            return

        if isinstance(file, str):
            file = [file]

        thread_ = ThreadCopyFiles(dest=dest, files=file)
        SignalsApp.all.btn_downloads_toggle.emit("show")
        cmd_ = lambda f: self.reveal_copied_files(thread_=thread_, files=f)
        thread_._finished.connect(cmd_)
        thread_.start()

    def reveal_copied_files(self, thread_: ThreadCopyFiles, files: list):

        MainUtils.reveal_files(files)

        if len(Dynamic.copy_threads) == 0:
            SignalsApp.all.btn_downloads_toggle.emit("hide")

        thread_.remove_threads()
