import os

from PyQt5.QtCore import QObject, pyqtSignal

from cfg import Dynamic

from .utils import URunnable, Utils


class WorkerSignals(QObject):
    finished_ = pyqtSignal(list)
    value_changed = pyqtSignal(int)
    text_changed = pyqtSignal(str)
    stop = pyqtSignal()


class ThreadCopyFiles(URunnable):
    def __init__(self, dest: str, files: list):
        super().__init__()
        self.signals_ = WorkerSignals()
        self.signals_.stop.connect(self.stop_copying)

        self.files = files
        self.dest = dest
        self.buffer_size = 1024*1024
        self.current_file = ""

        Dynamic.copy_threads.append(self)

    @URunnable.set_running_state
    def run(self):
        copied_size = 0
        files_dests = []

        try:
            total_size = sum(os.path.getsize(file) for file in self.files)
        except Exception as e:
            Utils.print_err(parent=self, error=e)
            self.signals_.value_changed.emit(100)
            self.signals_.finished_.emit(files_dests)
            self.remove_threads()
            return

        self.signals_.value_changed.emit(0)

        for file_path in self.files:

            if not self.should_run:
                self.signals_.value_changed.emit(100)
                self.signals_.finished_.emit(files_dests)
                Dynamic.copy_threads.remove(self)
                return

            dest_path = os.path.join(self.dest, os.path.basename(file_path))
            files_dests.append(dest_path)
            root, filename = os.path.split(file_path)
            self.signals_.text_changed.emit(filename)
            self.current_file = filename

            try:

                with open(file_path, 'rb') as fsrc, open(dest_path, 'wb') as fdest:

                    while self.should_run:

                        buf = fsrc.read(self.buffer_size)

                        if not buf:
                            break

                        fdest.write(buf)
                        copied_size += len(buf)
                        percent = int((copied_size / total_size) * 100)

                        self.signals_.value_changed.emit(percent)

            except Exception as e:
                Utils.print_err(parent=self, error=e)
                break
        
        self.signals_.value_changed.emit(100)
        self.signals_.finished_.emit(files_dests)
        Dynamic.copy_threads.remove(self)

    def stop_copying(self):
        self.should_run = False

    def get_current_file(self):
        return self.current_file