import os

from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QAction, QFileDialog, QLabel, QMainWindow, QWidget

from base_widgets import ContextCustom
from cfg import PSD_TIFF, Dynamic, JsonData
from signals import SignalsApp
from styles import Names, Themes
from utils.copy_files import ThreadCopyFiles
from utils.utils import UThreadPool, Utils

from ..win_smb import WinSmb
from ._load_thumbs import DbImage


class Shared:
    dialog = None

    @classmethod
    def show_smb(cls, parent_: QWidget | QMainWindow):

        if not isinstance(parent_, QMainWindow):
            parent_ = parent_.window()

        smb_win = WinSmb()
        smb_win.center_relative_parent(parent_)
        smb_win.show()


class CustomContext(ContextCustom):
    def __init__(self, files_list: list[DbImage], event):

        super().__init__(event=event)
        self.files_list = files_list

        save_jpg = QAction(text=Dynamic.lang.save_all_JPG, parent=self)
        save_jpg.triggered.connect(lambda: self.save_cmd(is_layers=False, save_as=False))
        self.addAction(save_jpg)

        save_layers = QAction(text=Dynamic.lang.save_all_layers, parent=self)
        save_layers.triggered.connect(lambda: self.save_cmd(is_layers=True, save_as=False))
        self.addAction(save_layers)

        self.addSeparator()

        save_as_jpg = QAction(text=Dynamic.lang.save_all_JPG_as, parent=self)
        save_as_jpg.triggered.connect(lambda: self.save_cmd(is_layers=False, save_as=True))
        self.addAction(save_as_jpg)

        save_as_layers = QAction(text=Dynamic.lang.save_all_layers_as, parent=self)
        save_as_layers.triggered.connect(lambda: self.save_cmd(is_layers=True, save_as=True))
        self.addAction(save_as_layers)

    def save_cmd(self, is_layers: bool, save_as: bool):

        if Utils.smb_check():

            if is_layers:
                images = [i.src for i in self.files_list if i.src.endswith(PSD_TIFF)]
            else:
                images = [i.src for i in self.files_list if not i.src.endswith(PSD_TIFF)]

            if save_as:
                self.dialog = QFileDialog()
                Shared.dialog = self.dialog
                self.dialog.setOption(QFileDialog.ShowDirsOnly, True)
                dest = self.dialog.getExistingDirectory()

                if not dest:
                    return

            else:
                dest = JsonData.down_folder
            
            self.copy_files_cmd(dest, images)

        else:
            Shared.show_smb(parent_=self)

    def copy_files_cmd(self, dest: str, files: list):
        if Utils.smb_check():
            self.copy_files_cmd_(dest, files)
        else:
            Shared.show_smb(parent_=self)

    def copy_files_cmd_(self, dest: str, files: list):
        files = [i for i in files if os.path.exists(i)]

        if len(files) == 0:
            return

        cmd_ = lambda files: self.copy_files_fin(files=files)
        copy_task = ThreadCopyFiles(dest=dest, files=files)
        copy_task.signals_.finished_.connect(cmd_)

        SignalsApp.all_.btn_downloads_toggle.emit("show")
        UThreadPool.pool.start(copy_task)

    def copy_files_fin(self, files: list):
        # self.reveal_files = Utils.reveal_files(files)
        if len(Dynamic.copy_threads) == 0:
            SignalsApp.all_.btn_downloads_toggle.emit("hide")


class Title(QLabel):
    def __init__(self, title: str, db_images: list, width: int):
        super().__init__(f"{title}. {Dynamic.lang.total}: {len(db_images)}")
        self.images = db_images
        self.setFixedWidth(width - 20)
        self.setWordWrap(True)
        self.setContentsMargins(0, 0, 0, 5)
        self.setObjectName(Names.th_title)
        self.setStyleSheet(Themes.current)

        self.my_context = None

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        try:
            self.my_context = CustomContext(files_list=self.images, event=ev)
            self.my_context.show_menu()
            # return super().contextMenuEvent(ev)
        except Exception as e:
            Utils.print_err(error=e)