import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QAction, QLabel, QSizePolicy

from base_widgets import ContextCustom
from cfg import PSD_TIFF, Dynamic, JsonData
from lang import Lang
from signals import SignalsApp
from styles import Names, Themes
from utils.copy_files import CopyFiles
from utils.utils import UThreadPool, Utils

from ..actions import OpenWins
from ._db_images import DbImage


class Title(QLabel):
    r_click = pyqtSignal()

    def __init__(self, title: str, db_images: list[DbImage], width: int):
        super().__init__(f"{title}. {Lang.total}: {len(db_images)}")
        self.db_images = db_images
        self.setContentsMargins(3, 5, 3, 5)
        self.setObjectName("th_title_new")
        self.setProperty("class", "normal")
        self.style().unpolish(self)
        self.style().polish(self)   
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Preferred
            )

    def save_cmd(self, is_layers: bool, save_as: bool):

        if Utils.smb_check():

            if is_layers:
                images = [
                    Utils.get_full_src(i.short_src)
                    for i in self.db_images
                    if i.short_src.endswith(PSD_TIFF)
                    ]
            else:
                images = [
                    Utils.get_full_src(i.short_src)
                    for i in self.db_images
                    if not i.short_src.endswith(PSD_TIFF)
                    ]

            if save_as:
                dialog = OpenWins.dialog_dirs()
                dest = dialog.getExistingDirectory()

                if not dest:
                    return

            else:
                dest = JsonData.down_folder
            
            self.copy_files_cmd(dest, images)

        else:
            OpenWins.smb(self.window())

    def copy_files_cmd(self, dest: str, files: list):
        if Utils.smb_check():
            self.copy_files_cmd_(dest, files)
        else:
            OpenWins.smb(self.window())

    def copy_files_cmd_(self, dest: str, files: list):
        files = [i for i in files if os.path.exists(i)]

        if len(files) == 0:
            return

        cmd_ = lambda files: self.copy_files_fin(files=files)
        copy_task = CopyFiles(dest=dest, files=files)
        copy_task.signals_.finished_.connect(cmd_)

        SignalsApp.all_.btn_downloads_toggle.emit("show")
        UThreadPool.pool.start(copy_task)

    def copy_files_fin(self, files: list):
        self.reveal_files = Utils.reveal_files(files)
        if len(CopyFiles.current_threads) == 0:
            SignalsApp.all_.btn_downloads_toggle.emit("hide")

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        self.r_click.emit()

        menu_ = ContextCustom(ev)

        self.setProperty("class", "selected")
        self.style().unpolish(self)
        self.style().polish(self)

        cmd_ = lambda: self.save_cmd(is_layers=False, save_as=False)
        save_jpg = QAction(text=Lang.save_all_JPG, parent=menu_)
        save_jpg.triggered.connect(cmd_)
        menu_.addAction(save_jpg)

        cmd_ = lambda: self.save_cmd(is_layers=True, save_as=False)
        save_layers = QAction(text=Lang.save_all_layers, parent=menu_)
        save_layers.triggered.connect(cmd_)
        menu_.addAction(save_layers)

        menu_.addSeparator()

        cmd_ = lambda: self.save_cmd(is_layers=False, save_as=True)
        save_as_jpg = QAction(text=Lang.save_all_JPG_as, parent=menu_)
        save_as_jpg.triggered.connect(cmd_)
        menu_.addAction(save_as_jpg)

        cmd_ = lambda: self.save_cmd(is_layers=True, save_as=True)
        save_as_layers = QAction(text=Lang.save_all_layers_as, parent=menu_)
        save_as_layers.triggered.connect(cmd_)
        menu_.addAction(save_as_layers)

        menu_.show_menu()

        self.setProperty("class", "normal")
        self.style().unpolish(self)
        self.style().polish(self)