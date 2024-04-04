from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QWidget

from cfg import cnf
from signals import gui_signals_app
from utils import FindTiffThread, MainUtils

from ..win_copy_files_thread import WinCopyFilesThread
from ..win_smb import WinSmb


class Manager:
    threads = []
    win_smb: WinSmb = None


class GuiThreadSaveFiles(QObject):
    finished = pyqtSignal()

    def __init__(
            self,
            parent: QWidget | QMainWindow,
            files: list,
            is_fiff: bool,
            is_downloads: bool
            ):

        super().__init__()
        Manager.threads.append(self)

        self.copy_files_win = None
        self.tiff_thread = None
        self.my_parent = parent

        self.tiff_list = []
        self.input_files = files

        self.is_tiff = is_fiff
        self.is_downloads = is_downloads

        if not MainUtils.smb_check():
            Manager.win_smb = WinSmb()
            Manager.win_smb.show()
            Manager.threads.remove(self)
            return

        if not isinstance(files, list):
            raise Exception("files must be list")

        if len(files) == 0:

            if cnf.scaner_running:
                t = f"{cnf.lng.no_tiff}. {cnf.lng.wait_scan_finished}"

            else:
                t = cnf.lng.no_tiff

            if isinstance(self.my_parent, QMainWindow):
                gui_signals_app.noti_img_view.emit(t)

            else:
                gui_signals_app.noti_main.emit(t)

            return

        if is_fiff:
            self.process_tiff_threads()
        else:
            self.run_save_files(self.input_files)

    def process_tiff_threads(self):
        self.current_index = 0
        self.next_tiff()

    def next_tiff(self):
        if self.current_index < len(self.input_files):
            self.tiff_thread = FindTiffThread(self.input_files[self.current_index])
            self.tiff_thread.finished.connect(self.add_to_tiff_list)
            self.tiff_thread.start()
        else:
            self.finish_find_tiffs()

    def add_to_tiff_list(self, tiff):
        self.tiff_list.append(tiff)
        self.current_index += 1
        self.next_tiff()

    def finish_find_tiffs(self):
        tiffs = [i for i in self.tiff_list if i]

        if len(tiffs) == 0:

            if cnf.scaner_running:
                t = f"{cnf.lng.no_tiff}. {cnf.lng.wait_scan_finished}"
            else:
                t = cnf.lng.no_tiff

            if isinstance(self.my_parent, QMainWindow):
                gui_signals_app.noti_img_view.emit(t)
            else:
                gui_signals_app.noti_main.emit(t)

            return

        else:
            self.run_save_files(tiffs)

    def run_save_files(self, files: list):
        if self.is_downloads:
            self.run_copy_files(files, cnf.down_folder)
            return

        dialog = QFileDialog()
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        selected_folder = dialog.getExistingDirectory()

        if selected_folder:
            self.run_copy_files(files, selected_folder)

    def run_copy_files(self, files: list, dest: str):
        self.copy_files_win = WinCopyFilesThread(files, dest)
        self.copy_files_win.finished.connect(self.finalize)

    def finalize(self):
        self.finished.emit()
        Manager.threads.remove(self)