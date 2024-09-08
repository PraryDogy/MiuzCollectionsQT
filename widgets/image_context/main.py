import os
from functools import partial

from PyQt5.QtWidgets import QAction, QFileDialog, QWidget

from base_widgets import ContextMenuBase, ContextSubMenuBase
from cfg import cnf
from signals import gui_signals_app
from utils import (MainUtils, RevealFiles, SendNotification, ThreadCopyFiles,
                   ThreadFindTiff)

from ..win_info import WinInfo
from ..win_smb import WinSmb


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
        reveal_jpg.triggered.connect(lambda: self.reveal_jpg(img_src=img_src))
        self.reveal_menu.addAction(reveal_jpg)

        self.reveal_menu.addSeparator()

        reveal_layers = QAction(parent=self, text=cnf.lng.layers)
        reveal_layers.triggered.connect(lambda: self.reveal_tiff(img_src=img_src))
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

    def select_thumbnail(self, img_src: str):
        if not cnf.image_viewer:
            try:
                cnf.selected_thumbnail.regular_style()
            except Exception as e:
                MainUtils.print_err(parent=self, error=e)

            try:
                cnf.selected_thumbnail = cnf.images[img_src]["widget"]
                cnf.selected_thumbnail.selected_style()
            except Exception as e:
                MainUtils.print_err(parent=self, error=e)

    def add_preview_item(self):
        open_action = QAction(cnf.lng.view, self)
        open_action.triggered.connect(
            lambda: self.show_image_viewer(self.img_src)
            )
        self.addAction(open_action)
        self.insertAction(self.info_action, open_action)

    def add_show_coll_item(self, collection: str):
        open_action = QAction(cnf.lng.open_collection, self)
        open_action.triggered.connect(lambda: self.load_collection(collection=collection))
        self.addAction(open_action)
        self.insertAction(self.info_action, open_action)

    def show_info_win(self, img_src: str):
        if MainUtils.smb_check():
            self.select_thumbnail(img_src=img_src)
            self.win_info = WinInfo(img_src=img_src, parent=self.my_parent)
            self.win_info.show()
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()
        
    def show_image_viewer(self, img_src: str):
        self.select_thumbnail(img_src=img_src)

        # prevent circular import
        from ..win_image_view import WinImageView
        self.win_img = WinImageView(parent=self.my_parent, img_src=img_src)
        self.win_img.show()

    def reveal_jpg(self, img_src: str):
        if MainUtils.smb_check():
            self.reveal_file_finish(img_src)
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()


    def reveal_tiff(self, img_src: str):
        if MainUtils.smb_check():
            self.reveal_tiff_task = ThreadFindTiff(img_src)

            self.reveal_tiff_task.finished.connect(lambda tiff: self.reveal_file_finish(tiff))
            self.reveal_tiff_task.can_remove.connect(self.reveal_tiff_task.remove_threads)

            self.reveal_tiff_task.start()
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()

    def reveal_file_finish(self, file: str):
        if not os.path.exists(file):
            SendNotification(cnf.lng.no_file)
            return
        RevealFiles([file])

    def save_as_jpg(self, img_src: str):
        if MainUtils.smb_check():
            dest = self.select_folder()
            if dest:
                self.copy_file(dest=dest, file=img_src)
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()

    def save_jpg(self, img_src: str):
        if MainUtils.smb_check():
            self.copy_file(dest=cnf.down_folder, file=img_src)
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()

    def save_as_tiffs(self, img_src: str):
        if MainUtils.smb_check():
            dest = self.select_folder()
            if dest:
                self.find_tiffs(dest=dest, img_src=img_src)
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()

    def save_tiffs(self, img_src: str):
        if MainUtils.smb_check():
            self.find_tiffs(dest=cnf.down_folder, img_src=img_src)
        else:
            self.smb_win = WinSmb(parent=self.my_parent)
            self.smb_win.show()
        
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
        gui_signals_app.show_downloads.emit()
        self.copy_task.finished.connect(lambda files: self.copy_files_fin(self.copy_task, files))
        self.copy_task.start()

    def copy_files_fin(self, copy_task: ThreadCopyFiles, files: list):
        self.reveal_files = RevealFiles(files)
        if len(cnf.copy_threads) == 0:
            gui_signals_app.hide_downloads.emit()
        try:
            copy_task.remove_threads()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

    def load_collection(self, collection: str):
        cnf.curr_coll = collection
        cnf.current_photo_limit = cnf.LIMIT
        gui_signals_app.reload_title.emit()
        gui_signals_app.scroll_top.emit()
        gui_signals_app.reload_menu.emit()
        gui_signals_app.reload_thumbnails.emit()

        # self.select_thumbnail(img_src=self.img_src)
        # gui_signals_app.move_to_wid.emit(cnf.selected_thumbnail)