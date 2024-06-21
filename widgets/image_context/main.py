import os
from functools import partial

from PyQt5.QtWidgets import QAction, QFileDialog, QWidget

from base_widgets import ContextMenuBase, ContextSubMenuBase
from cfg import cnf
from utils import (RevealFiles, SendNotification, ThreadCopyFiles,
                   ThreadFindTiff)

from ..win_copy_files import WinCopyFiles
from ..win_info import WinInfo


class Shared:
    file_dialog = None

class ImageContext(ContextMenuBase):
    def __init__(self, img_src: str, event, parent: QWidget = None):
        super().__init__(event)

        self.my_parent = parent
        self.img_src = img_src
        
        self.info_action = QAction(text=cnf.lng.info, parent=self)
        self.info_action.triggered.connect(partial(self.show_info_win, img_src))
        self.addAction(self.info_action)

        self.addSeparator()

        self.reveal_menu = ContextSubMenuBase(parent=self, title=cnf.lng.reveal_in_finder)
        self.addMenu(self.reveal_menu)

        reveal_jpg = QAction(parent=self, text="JPG")
        reveal_jpg.triggered.connect(lambda: self.reveal_jpg(img_src))
        self.reveal_menu.addAction(reveal_jpg)

        self.reveal_menu.addSeparator()

        reveal_layers = QAction(parent=self, text=cnf.lng.layers)
        reveal_layers.triggered.connect(lambda: self.reveal_tiff(img_src))
        self.reveal_menu.addAction(reveal_layers)

        self.addSeparator()

        save_as_menu = ContextSubMenuBase(parent=self, title=cnf.lng.save_image_in)
        self.addMenu(save_as_menu)

        save_as_jpg = QAction(parent=self, text="JPG")
        save_as_jpg.triggered.connect(lambda: self.save_as_jpg(img_src))
        save_as_menu.addAction(save_as_jpg)

        save_as_menu.addSeparator()

        save_as_layers = QAction(text=cnf.lng.layers, parent=self)
        save_as_layers.triggered.connect(lambda: self.save_as_tiffs(img_src))
        save_as_menu.addAction(save_as_layers)

        save_menu = ContextSubMenuBase(parent=self, title=cnf.lng.save_image_downloads)
        self.addMenu(save_menu)

        save_jpg = QAction(text="JPG", parent=self)
        save_jpg.triggered.connect(lambda: self.save_jpg(img_src))
        save_menu.addAction(save_jpg)

        save_menu.addSeparator()

        save_layers = QAction(text=cnf.lng.layers, parent=self)
        save_layers.triggered.connect(lambda: self.save_tiffs(img_src))
        save_menu.addAction(save_layers)

    def add_preview_item(self):
        open_action = QAction(cnf.lng.view, self)
        open_action.triggered.connect(
            lambda: self.show_image_viewer(self.img_src)
            )
        self.addAction(open_action)
        self.insertAction(self.info_action, open_action)

    def show_info_win(self, img_src: str):
        self.win_info = WinInfo(img_src=img_src, parent=self.my_parent)
        self.win_info.show()
        
    def show_image_viewer(self, img_src: str):
        # import here to prevent circular import
        from ..win_image_view import WinImageView
        self.win_img = WinImageView(parent=self.my_parent, img_src=img_src)
        self.win_img.show()

    def reveal_jpg(self, img_src: str):
        self.reveal_file_finish(img_src)

    def reveal_tiff(self, img_src: str):
        self.reveal_tiff_task = ThreadFindTiff(img_src)

        self.reveal_tiff_task.finished.connect(lambda tiff: self.reveal_file_finish(tiff))
        self.reveal_tiff_task.can_remove.connect(self.reveal_tiff_task.remove_threads)

        self.reveal_tiff_task.start()

    def reveal_file_finish(self, file: str):
        if not os.path.exists(file):
            SendNotification(cnf.lng.no_file)
            return
        RevealFiles([file])

    def save_as_jpg(self, img_src: str):
        dest = self.select_folder()
        if dest:
            self.copy_file(dest=dest, file=img_src)

    def save_jpg(self, img_src: str):
        self.copy_file(dest=cnf.down_folder, file=img_src)

    def save_as_tiffs(self, img_src: str):
        dest = self.select_folder()
        if dest:
            self.find_tiffs(dest=dest, img_src=img_src)

    def save_tiffs(self, img_src: str):
        self.find_tiffs(dest=cnf.down_folder, img_src=img_src)
        
    def find_tiffs(self, dest: str, img_src: str):
        self.find_tiff_task = ThreadFindTiff(img_src)

        self.find_tiff_task.finished.connect(lambda tiff: self.copy_file(dest, tiff))
        self.find_tiff_task.can_remove.connect(self.find_tiff_task.remove_threads)

        self.find_tiff_task.start()

    def select_folder(self):
        self.save_dialog = QFileDialog()
        self.save_dialog.setOption(QFileDialog.ShowDirsOnly, True)
        selected_folder = self.save_dialog.getExistingDirectory()
        Shared.file_dialog = self.save_dialog

        if selected_folder:
            return selected_folder
        return None
    
    def copy_file(self, dest: str, file: str):
        if not file or not os.path.exists(file):
            SendNotification(cnf.lng.no_file)
            return

        self.copy_task = ThreadCopyFiles(dest=dest, files=[file])
        copy_win = WinCopyFiles(parent=self.my_parent)

        self.copy_task.value_changed.connect(lambda val: copy_win.set_value(val))
        self.copy_task.finished.connect(lambda files: self.copy_files_fin(self.copy_task, copy_win, files))
        copy_win.cancel_sign.connect(lambda: self.copy_files_cancel(self.copy_task, copy_win))
        
        copy_win.show()
        self.copy_task.start()

    def copy_files_fin(self, copy_task: ThreadCopyFiles, copy_win: WinCopyFiles, files: list):
        self.reveal_files = RevealFiles(files)
        try:
            copy_task.remove_threads()
            copy_win.close()
        except Exception as e:
            print(e)

    def copy_files_cancel(self, copy_task: ThreadCopyFiles, copy_win: WinCopyFiles):
        try:
            copy_task.stop.emit()
            copy_task.remove_threads()
            copy_win.close()
        except Exception as e:
            print(e)
