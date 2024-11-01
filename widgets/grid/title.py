import os

from .db_images import DbImage
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QAction, QFileDialog, QLabel, QWidget

from base_widgets import ContextMenuBase
from cfg import PSD_TIFF, cnf
from signals import signals_app
from styles import Names, Themes
from utils.copy_files import ThreadCopyFiles
from utils.main_utils import MainUtils

from ..win_smb import WinSmb


class Shared:
    dialog = None


class CustomContext(ContextMenuBase):
    def __init__(self, parent: QWidget, files_list: list[DbImage], event):

        super().__init__(event=event)
        self.my_parent = parent
        self.files_list = files_list

        save_jpg = QAction(text=cnf.lng.save_all_JPG, parent=self)
        save_jpg.triggered.connect(lambda: self.save_cmd(is_layers=False, save_as=False))
        self.addAction(save_jpg)

        save_layers = QAction(text=cnf.lng.save_all_layers, parent=self)
        save_layers.triggered.connect(lambda: self.save_cmd(is_layers=True, save_as=False))
        self.addAction(save_layers)

        self.addSeparator()

        save_as_jpg = QAction(text=cnf.lng.save_all_JPG_as, parent=self)
        save_as_jpg.triggered.connect(lambda: self.save_cmd(is_layers=False, save_as=True))
        self.addAction(save_as_jpg)

        save_as_layers = QAction(text=cnf.lng.save_all_layers_as, parent=self)
        save_as_layers.triggered.connect(lambda: self.save_cmd(is_layers=True, save_as=True))
        self.addAction(save_as_layers)

    def save_cmd(self, is_layers: bool, save_as: bool):

        if MainUtils.smb_check():

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
                dest = cnf.down_folder
            
            self.copy_files_cmd(dest, images)

        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()

    def copy_files_cmd(self, dest: str, files: list):
        files = [i for i in files if os.path.exists(i)]

        if len(files) == 0:
            MainUtils.send_notification(cnf.lng.no_file)
            return

        copy_task = ThreadCopyFiles(dest=dest, files=files)
        signals_app.show_downloads.emit()
        copy_task.finished.connect(lambda files: self.copy_files_fin(copy_task, files=files))
        copy_task.start()

    def copy_files_fin(self, copy_task: ThreadCopyFiles, files: list):
        self.reveal_files = MainUtils.reveal_files(files)
        if len(cnf.copy_threads) == 0:
            signals_app.hide_downloads.emit()
        try:
            copy_task.remove_threads()                
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)


class Title(QLabel):
    def __init__(self, title: str, db_images: list, width: int):
        super().__init__(f"{title}. {cnf.lng.total}: {len(db_images)}")
        self.images = db_images
        self.setFixedWidth(width - 20)
        self.setWordWrap(True)
        self.setContentsMargins(0, 0, 0, 5)
        self.setObjectName(Names.th_title)
        self.setStyleSheet(Themes.current)

        self.my_context = None

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        try:
            self.my_context = CustomContext(parent=self, files_list=self.images, event=ev)
            self.my_context.show_menu()
            return super().contextMenuEvent(ev)
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)