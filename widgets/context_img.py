import os
from functools import partial

from PyQt5.QtWidgets import QAction, QFileDialog, QWidget

from base_widgets import ContextMenuBase
from cfg import Dynamic, JsonData
from signals import signals_app
from utils.copy_files import ThreadCopyFiles
from utils.main_utils import MainUtils

from .win_info import WinInfo
from .win_smb import WinSmb


class Shared:
    file_dialog: QFileDialog = None


class ContextImg(ContextMenuBase):
    def __init__(self, src: str, event, parent: QWidget = None):
        super().__init__(event)

        self.my_parent = parent
        self.src = src
        
        self.info_action = QAction(text=Dynamic.lng.info, parent=self)
        self.info_action.triggered.connect(partial(self.show_info_win, src))
        self.addAction(self.info_action)

        self.addSeparator()

        copy_action = QAction(parent=self, text=Dynamic.lng.copy_path)
        copy_action.triggered.connect(lambda: MainUtils.copy_text(src))
        self.addAction(copy_action)

        reveal_action = QAction(parent=self, text=Dynamic.lng.reveal_in_finder)
        reveal_action.triggered.connect(self.reveal_cmd)
        self.addAction(reveal_action)

        save_as_action = QAction(parent=self, text=Dynamic.lng.save_image_in)
        save_as_action.triggered.connect(self.save_as_cmd)
        self.addAction(save_as_action)

        save_menu = QAction(parent=self, text=Dynamic.lng.save_image_downloads)
        save_menu.triggered.connect(self.save_cmd)
        self.addAction(save_menu)

    def add_preview_item(self):
        open_action = QAction(Dynamic.lng.view, self)
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
        signals_app.win_img_view_open_in.emit(self.my_parent)

    def reveal_cmd(self):
        if MainUtils.smb_check():
            if not os.path.exists(self.src):
                MainUtils.send_notification(Dynamic.lng.no_file)
            else:
                MainUtils.reveal_files([self.src])
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()

    def save_as_cmd(self):
        if MainUtils.smb_check():

            Shared.file_dialog = QFileDialog()
            Shared.file_dialog.setOption(QFileDialog.ShowDirsOnly, True)
            dest = Shared.file_dialog.getExistingDirectory()

            if dest:
                self.copy_files_cmd(dest=dest, file=self.src)

        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()   

    def save_cmd(self):
        if MainUtils.smb_check():
            self.copy_files_cmd(dest=JsonData.down_folder, file=self.src)
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()
    
    def copy_files_cmd(self, dest: str, file: str):

        if not file or not os.path.exists(file):
            MainUtils.send_notification(Dynamic.lng.no_file)
            return

        self.copy_task = ThreadCopyFiles(dest=dest, files=[file])
        signals_app.btn_downloads_hide.emit(False)
        self.copy_task.finished.connect(lambda files: self.copy_files_fin(self.copy_task, files))
        self.copy_task.start()

    def copy_files_fin(self, copy_task: ThreadCopyFiles, files: list):
        self.reveal_files = MainUtils.reveal_files(files)
        if len(Dynamic.copy_threads) == 0:
            signals_app.btn_downloads_hide.emit(True)
        try:
            copy_task.remove_threads()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)
