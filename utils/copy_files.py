import os
from time import sleep

from PyQt5.QtCore import QThread, pyqtSignal

from .reveal_files import RevealFiles


class CopyFilesThread(QThread):
    finished = pyqtSignal(list)
    value = pyqtSignal(int)
    stop = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.stop.connect(self.stop_copying)
        self.flag = True

    def set_sources(self, dest_folder: str, source_files: list):
        self.source_files = source_files
        self.dest_folder = dest_folder
        self.buffer_size = 1024*1024

    def run(self):
        total_size = sum(os.path.getsize(file) for file in self.source_files)
        copied_size = 0
        files_dests = []

        self.value.emit(0)

        for file_path in self.source_files:

            if not self.flag:
                return

            dest_path = os.path.join(self.dest_folder, os.path.basename(file_path))
            files_dests.append(dest_path)

            with open(file_path, 'rb') as fsrc, open(dest_path, 'wb') as fdest:

                while self.flag:

                    buf = fsrc.read(self.buffer_size)

                    if not buf:
                        break

                    fdest.write(buf)
                    copied_size += len(buf)
                    percent = int((copied_size / total_size) * 100)

                    self.value.emit(percent)
        
        self.value.emit(100)
        self.finished.emit(files_dests)
        RevealFiles(files_dests)

    def stop_copying(self):
        self.flag = False
