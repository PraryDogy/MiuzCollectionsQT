import os
from time import sleep

from PyQt5.QtCore import QThread, pyqtSignal


class Manager:
    threads = []


class ThreadCopyFiles(QThread):
    finished = pyqtSignal(list)
    value_changed = pyqtSignal(int)
    stop = pyqtSignal()

    def __init__(self, dest: str, files: list):
        super().__init__()
        self.stop.connect(self.stop_copying)
        self.flag = True

        self.files = files
        self.dest = dest
        self.buffer_size = 1024*1024

    def run(self):
        Manager.threads.append(self)
        copied_size = 0
        files_dests = []

        try:
            total_size = sum(os.path.getsize(file) for file in self.files)
        except Exception as e:
            print(e)
            self.value_changed.emit(100)
            self.finished.emit(files_dests)
            Manager.threads.remove(self)
            return

        self.value_changed.emit(0)

        for file_path in self.files:

            if not self.flag:
                return

            dest_path = os.path.join(self.dest, os.path.basename(file_path))
            files_dests.append(dest_path)

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
                print(e)
                break
        
        self.value_changed.emit(100)
        self.finished.emit(files_dests)
        Manager.threads.remove(self)

    def stop_copying(self):
        self.flag = False
