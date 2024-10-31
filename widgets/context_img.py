import os
from functools import partial

from PyQt5.QtWidgets import QAction, QFileDialog, QWidget

from base_widgets import ContextMenuBase
from cfg import cnf
from signals import signals_app
from utils.main_utils import MainUtils
from utils.copy_files import ThreadCopyFiles

from .win_info import WinInfo
from .win_smb import WinSmb


class Shared:
    file_dialog: QFileDialog = None


class ContextImg(ContextMenuBase):
    def __init__(self, img_src: str, event, parent: QWidget = None):
        super().__init__(event)

        self.my_parent = parent
        self.img_src = img_src
        
        self.info_action = QAction(text=cnf.lng.info, parent=self)
        self.info_action.triggered.connect(partial(self.show_info_win, img_src))
        self.addAction(self.info_action)

        self.addSeparator()

        reveal_action = QAction(parent=self, text=cnf.lng.reveal_in_finder)
        reveal_action.triggered.connect(self.reveal_cmd)
        self.addAction(reveal_action)

        save_as_action = QAction(parent=self, text=cnf.lng.save_image_in)
        save_as_action.triggered.connect(self.save_as_cmd)
        self.addAction(save_as_action)

        save_menu = QAction(parent=self, text=cnf.lng.save_image_downloads)
        save_menu.triggered.connect(self.save_cmd)
        self.addAction(save_menu)

    def add_preview_item(self):
        open_action = QAction(cnf.lng.view, self)
        open_action.triggered.connect(self.show_image_viewer)
        self.addAction(open_action)
        self.insertAction(self.info_action, open_action)

    def show_info_win(self, img_src: str):
        if MainUtils.smb_check():
            self.win_info = WinInfo(src=img_src, parent=self.my_parent)
            self.win_info.show()
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()
        
    def show_image_viewer(self):
        from .win_image_view import WinImageView
        self.win_img = WinImageView(parent=self.my_parent, src=self.img_src)
        self.win_img.show()

    def reveal_cmd(self):
        if MainUtils.smb_check():
            if not os.path.exists(self.img_src):
                MainUtils.send_notification(cnf.lng.no_file)
            else:
                MainUtils.reveal_files([self.img_src])
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()

    def save_as_cmd(self):
        if MainUtils.smb_check():

            Shared.file_dialog = QFileDialog()
            Shared.file_dialog.setOption(QFileDialog.ShowDirsOnly, True)
            dest = Shared.file_dialog.getExistingDirectory()

            if dest:
                self.copy_files_cmd(dest=dest, file=self.img_src)

        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()   

    def save_cmd(self):
        if MainUtils.smb_check():
            self.copy_files_cmd(dest=cnf.down_folder, file=self.img_src)
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()
    
    def copy_files_cmd(self, dest: str, file: str):

        if not file or not os.path.exists(file):
            MainUtils.send_notification(cnf.lng.no_file)
            return

        self.copy_task = ThreadCopyFiles(dest=dest, files=[file])
        signals_app.show_downloads.emit()
        self.copy_task.finished.connect(lambda files: self.copy_files_fin(self.copy_task, files))
        self.copy_task.start()

    def copy_files_fin(self, copy_task: ThreadCopyFiles, files: list):
        self.reveal_files = MainUtils.reveal_files(files)
        if len(cnf.copy_threads) == 0:
            signals_app.hide_downloads.emit()
        try:
            copy_task.remove_threads()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)
