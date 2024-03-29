from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QMainWindow

from cfg import cnf
from signals import gui_signals_app
from utils import FindTiffThread, RevealFiles


class Manager:
    threads = []


class GuiThreadRevealFiles(QObject):
    finished = pyqtSignal()

    def __init__(
            self,
            parent: QWidget | QMainWindow,
            files: list,
            is_tiff: bool
            ) -> None:

        super().__init__()
        Manager.threads.append(self)

        self.input_files: list = files
        self.tiff_list = []
        self.current_index = 0
        self.my_parent = parent

        self.tiff_thread = None
        self.reveal_app = None

        if not isinstance(files, list):
            raise Exception("files must be list")

        if is_tiff:
            self.process_tiff_threads()
        else:
            self.run_reveal(self.input_files)

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
            self.run_reveal(tiffs)

    def run_reveal(self, files: list):
        self.reveal_app = RevealFiles(files)
        self.reveal_app.finished.connect(self.finalize)

    def finalize(self):
        self.finished.emit()
        Manager.threads.remove(self)
