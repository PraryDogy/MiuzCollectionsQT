import os

from PyQt5.QtWidgets import QAction, QFileDialog, QMenu

from cfg import cnf
from utils.copy_files import ThreadCopyFiles
from utils.find_tiffs import ThreadFindTiff
from utils.main_utils import MainUtils
from utils.reveal_files import RevealFiles
from utils.send_notification import SendNotification

from ..win_copy_files import WinCopyFiles


class MyDialog(QFileDialog):
    def __init__(self):
        super().__init__()
        self.setOption(QFileDialog.ShowDirsOnly, True)


class RevealJpg(QAction):
    def __init__(self, parent: QMenu, img_src: str):
        super().__init__(parent=parent, text="JPG")
        self.triggered.connect(lambda: self.reveal(img_src=img_src))

    def reveal(self, img_src: str):
        if not os.path.exists(img_src):
            SendNotification(cnf.lng.no_file)
            return
        RevealFiles(files_list=[img_src])


class RevealLayers(QAction):
    def __init__(self, parent: QMenu, img_src: str):
        super().__init__(parent=parent, text=cnf.lng.layers)
        self.triggered.connect(lambda: self.reveal_start(img_src=img_src))
        self.task = None

    def reveal_start(self, img_src: str):
        self.task = ThreadFindTiff(img_src)
        self.task.finished.connect(lambda tiff: self.reveal_finish(tiff))
        self.task.start()

    def reveal_finish(self, tiff: str):
        self.task.remove_threads()

        if not os.path.exists(tiff):
            SendNotification(cnf.lng.no_file)
            return
        RevealFiles([tiff])


class SaveJpg(QAction):
    def __init__(self, parent: QMenu, img_src: str, dest: str = None):
        super().__init__(parent=parent, text="JPG")
        self.triggered.connect(lambda: self.prepare(img_src=img_src, dest=dest))
        self.task = None

    def prepare(self, img_src: str, dest: str):
        if not os.path.exists(img_src):
            SendNotification(cnf.lng.no_file)
            return
        
        if not dest:
            self.dialog = MyDialog()
            dest = self.dialog.getExistingDirectory()
            if dest:
                self.start_copying(img_src=img_src, dest=dest)

        else:
            self.start_copying(img_src=img_src, dest=dest)

    def start_copying(self, img_src: str, dest: str):
        self.task = ThreadCopyFiles(dest=dest, files=[img_src])
        self.copy_win = WinCopyFiles(parent=self.parent())

        self.copy_win.cancel_pressed.connect(self.task.stop.emit)

        self.task.value_changed.connect(lambda val: self.copy_win.set_value(value=val))
        self.task.finished.connect(lambda dest_list: self.finish_copying(dest_list=dest_list))

        self.copy_win.show()
        self.task.start()

    def finish_copying(self, dest_list: list):
        try:
            self.copy_win.close()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

        try:
            self.task.remove_threads()
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)

        RevealFiles(files_list=dest_list)