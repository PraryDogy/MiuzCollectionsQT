import os

from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QAction, QFileDialog, QLabel, QWidget

from base_widgets import ContextMenuBase, ContextSubMenuBase
from cfg import cnf
from styles import Names, Themes
from utils import (MainUtils, RevealFiles, SendNotification, ThreadCopyFiles,
                   ThreadFindTiffsMultiple)

from ..win_smb import WinSmb
from signals import gui_signals_app

class Shared:
    dialog = None


class CustomContext(ContextMenuBase):
    def __init__(self, parent: QWidget, files_list: list, event):

        super().__init__(event=event)
        self.my_parent = parent

        save_as_menu = ContextSubMenuBase(parent=self, title=cnf.lng.save_group_in)
        self.addMenu(save_as_menu)

        save_as_jpg = QAction(text="JPG", parent=self)
        save_as_jpg.triggered.connect(lambda: self.save_as_jpg(files_list))
        save_as_menu.addAction(save_as_jpg)

        save_as_menu.addSeparator()

        save_as_layers = QAction(text=cnf.lng.layers, parent=self)
        save_as_layers.triggered.connect(lambda: self.save_as_tiffs(files_list))
        save_as_menu.addAction(save_as_layers)

        self.addSeparator()

        save_menu = ContextSubMenuBase(parent=self, title=cnf.lng.save_group_downloads)
        self.addMenu(save_menu)

        save_jpg = QAction(text="JPG", parent=self)
        save_jpg.triggered.connect(lambda: self.save_jpg(files_list))
        save_menu.addAction(save_jpg)

        save_menu.addSeparator()

        save_layers = QAction(text=cnf.lng.layers, parent=self)
        save_layers.triggered.connect(lambda: self.save_tiffs(files_list))
        save_menu.addAction(save_layers)
        self.save_as_win = None

    def save_as_jpg(self, files_list: list):
        if MainUtils.smb_check():
            dest = self.select_folder()
            if dest:
                self.copy_files(dest, files_list)
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()

    def save_as_tiffs(self, files_list):
        if MainUtils.smb_check():
            dest = self.select_folder()
            if dest:
                self.find_tiffs(dest, files_list)
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()

    def save_jpg(self, files_list: list):
        if MainUtils.smb_check():
            self.copy_files(cnf.down_folder, files_list)
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()

    def save_tiffs(self, files_list: list):
        if MainUtils.smb_check():
            self.find_tiffs(cnf.down_folder, files_list)
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()
        
    def find_tiffs(self, dest: str, files_list: list):
        tsk = ThreadFindTiffsMultiple(files_list)
        tsk.finished.connect(lambda tiff_list: self.copy_files(dest, tiff_list))
        tsk.can_remove.connect(tsk.remove_threads)

        tsk.start()

    def select_folder(self):
        self.dialog = QFileDialog()
        Shared.dialog = self.dialog
        self.dialog.setOption(QFileDialog.ShowDirsOnly, True)
        selected_folder = self.dialog.getExistingDirectory()

        if selected_folder:
            return selected_folder
        return None

    def copy_files(self, dest: str, files: list):
        files = [i for i in files if os.path.exists(i)]

        if len(files) == 0:
            SendNotification(cnf.lng.no_file)
            return

        copy_task = ThreadCopyFiles(dest=dest, files=files)
        gui_signals_app.show_downloads.emit()
        copy_task.finished.connect(lambda files: self.copy_files_fin(copy_task, files=files))
        copy_task.start()

    def copy_files_fin(self, copy_task: ThreadCopyFiles, files: list):
        self.reveal_files = RevealFiles(files)
        if len(cnf.copy_threads) == 0:
            gui_signals_app.hide_downloads.emit()
        try:
            copy_task.remove_threads()                
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)


class Title(QLabel):
    def __init__(self, title: str, images: list, width: int):

        super().__init__(f"{title}. {cnf.lng.total}: {len(images)}")
        self.setFixedWidth(width - 20)
        self.setWordWrap(True)
        self.setContentsMargins(0, 0, 0, 5)
        self.setObjectName(Names.th_title)
        self.setStyleSheet(Themes.current)

        self.images = images
        self.my_context = None

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:
        try:
            self.my_context = CustomContext(parent=self, files_list=self.images, event=ev)
            self.my_context.show_menu()
            return super().contextMenuEvent(ev)
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)