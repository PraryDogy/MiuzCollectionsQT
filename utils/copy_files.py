import os

from PyQt5.QtCore import pyqtSignal

from cfg import cnf

from .main_utils import MainUtils
from .my_thread import MyThread


class ThreadCopyFiles(MyThread):
    finished = pyqtSignal(list)
    value_changed = pyqtSignal(int)
    text_changed = pyqtSignal(str)
    stop = pyqtSignal()

    def __init__(self, dest: str, files: list):
        super().__init__(parent=None)
        self.stop.connect(self.stop_copying)
        self.flag = True

        self.files = files
        self.dest = dest
        self.buffer_size = 1024*1024

        cnf.copy_threads.append(self)

    def run(self):
        copied_size = 0
        files_dests = []

        try:
            total_size = sum(os.path.getsize(file) for file in self.files)
        except Exception as e:
            MainUtils.print_err(parent=self, error=e)
            self.value_changed.emit(100)
            self.finished.emit(files_dests)
            self.remove_threads()
            return

        self.value_changed.emit(0)

        for file_path in self.files:

            if not self.flag:
                return

            dest_path = os.path.join(self.dest, os.path.basename(file_path))
            files_dests.append(dest_path)
            root, filename = os.path.split(file_path)
            self.text_changed.emit(filename)

            try:

                with open(file_path, 'rb') as fsrc, open(dest_path, 'wb') as fdest:

                    while self.flag:

                        buf = fsrc.read(self.buffer_size)

                        if not buf:
                            break

                        fdest.write(buf)
                        copied_size += len(buf)
                        percent = int((copied_size / total_size) * 100)

                        self.value_changed.emit(percent)

            except Exception as e:
                MainUtils.print_err(parent=self, error=e)
                self.remove_threads()
                break
        
        self.value_changed.emit(100)
        self.finished.emit(files_dests)
        self.remove_threads()
        cnf.copy_threads.remove(self)

    def stop_copying(self):
        self.flag = False
