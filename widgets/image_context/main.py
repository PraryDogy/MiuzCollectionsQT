from functools import partial

from PyQt5.QtWidgets import QAction, QFileDialog, QWidget

from base_widgets import ContextMenuBase, ContextSubMenuBase
from cfg import cnf
from utils import RevealFiles, ThreadCopyFiles, ThreadFindTiff, SendNotification

from ..win_copy_files import WinCopyFiles
from ..win_info import WinInfo
import os

class Manager:
    win_info = None
    win_image_view = None
    dialog = None
    copy_files_wins = []
    threads = []


# We save some items to the Manager. We want to prevent the widget/thread 
# from being destroyed if the parent widgets are reinitialized.
# for example reinit images grid


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


        self.reveal_files = None
        self.tiff_thread = None
        self.save_files = None

    def add_preview_item(self):
        open_action = QAction(cnf.lng.view, self)
        open_action.triggered.connect(
            lambda: self.show_image_viewer(self.img_src)
            )
        self.addAction(open_action)
        self.insertAction(self.info_action, open_action)

    def show_info_win(self, img_src):
        Manager.win_info = WinInfo(img_src, self.my_parent)
        Manager.win_info.show()
        
    def show_image_viewer(self, img_src):
        # import here to prevent circular import
        from ..win_image_view import WinImageView
        Manager.win_image_view = WinImageView(img_src)
        Manager.win_image_view.show()

    def reveal_jpg(self, img_src: str):
        self.reveal_file_finish(img_src)

    def reveal_tiff(self, img_src: str):
        tiff_task = ThreadFindTiff(img_src)
        Manager.threads.append(tiff_task)

        tiff_task.finished.connect(lambda tiff: self.reveal_file_finish(tiff))
        tiff_task.can_remove.connect(lambda: Manager.threads.remove(tiff_task))

        tiff_task.run()

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
        tiff_task = ThreadFindTiff(img_src)
        Manager.threads.append(tiff_task)

        tiff_task.finished.connect(lambda tiff: self.copy_file(dest, tiff))
        tiff_task.can_remove.connect(lambda: Manager.threads.remove(tiff_task))

        tiff_task.run()

    def select_folder(self):
        Manager.dialog = QFileDialog()
        Manager.dialog.setOption(QFileDialog.ShowDirsOnly, True)
        selected_folder = Manager.dialog.getExistingDirectory()

        if selected_folder:
            return selected_folder
        return None
    
    def copy_file(self, dest: str, file: str):
        if not file:
            SendNotification(cnf.lng.no_file)
            return

        copy_task = ThreadCopyFiles(dest=dest, files=[file])
        copy_win = WinCopyFiles(parent=self.my_parent)

        Manager.threads.append(copy_task)
        Manager.copy_files_wins.append(copy_win)

        copy_task.value_changed.connect(lambda val: copy_win.set_value(val))
        copy_task.finished.connect(lambda files: self.copy_files_fin(copy_task, copy_win, files=files))
        copy_win.cancel_sign.connect(lambda: self.copy_files_cancel(copy_task, copy_win))
        
        copy_win.show()
        copy_task.run()

    def copy_files_fin(self, copy_task: ThreadCopyFiles, copy_win: WinCopyFiles, files: list):
        self.reveal_files = RevealFiles(files)
        Manager.threads.remove(copy_task)
        Manager.copy_files_wins.remove(copy_win)
        copy_win.deleteLater()

    def copy_files_cancel(self, copy_task: ThreadCopyFiles, copy_win: WinCopyFiles):
        copy_task.stop.emit()
        Manager.threads.remove(copy_task)
        Manager.copy_files_wins.remove(copy_win)
        copy_win.deleteLater()