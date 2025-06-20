import os

from PyQt5.QtCore import QObject, QRunnable, QThreadPool, QTimer, pyqtSignal
from sqlalchemy import update

from database import THUMBS, Dbase
from main_folder import MainFolder
from signals import SignalsApp

from .utils import Utils


class URunnable(QRunnable):
    def __init__(self):
        """
        Переопределите метод task().
        Не переопределяйте run().
        """
        super().__init__()
        self.should_run__ = True
        self.finished__ = False

    def is_should_run(self):
        return self.should_run__
    
    def set_should_run(self, value: bool):
        self.should_run__ = value

    def set_finished(self, value: bool):
        self.finished__ = value

    def is_finished(self):
        return self.finished__
    
    def run(self):
        try:
            self.task()
        finally:
            self.set_finished(True)
            if self in UThreadPool.tasks:
                QTimer.singleShot(5000, lambda: UThreadPool.tasks.remove(self))

    def task(self):
        raise NotImplementedError("Переопредели метод task() в подклассе.")
    

class UThreadPool:
    pool: QThreadPool = None
    tasks: list[URunnable] = []

    @classmethod
    def init(cls):
        cls.pool = QThreadPool.globalInstance()

    @classmethod
    def start(cls, runnable: URunnable):
        cls.tasks.append(runnable)
        cls.pool.start(runnable)


class CopyFilesSignals(QObject):
    finished_ = pyqtSignal(list)
    value_changed = pyqtSignal(int)
    stop = pyqtSignal()


class CopyFiles(URunnable):
    current_threads: list["CopyFiles"] = []
    list_of_file_lists: list[list[str]] = []

    def __init__(self, dest: str, files: list, move_files: bool):
        """
        Если move_files установить на True, то исходные файлы будут удалены
        по законам перемещения
        """
        super().__init__()
        self.signals_ = CopyFilesSignals()
        self.signals_.stop.connect(self.stop_cmd)
        self.files = files
        self.dest = dest
        self.move_files = move_files

    def task(self):
        CopyFiles.current_threads.append(self)
        SignalsApp.instance.win_downloads_open.emit()

        copied_size = 0
        files_dests = []

        try:
            total_size = sum(os.path.getsize(file) for file in self.files)
        except Exception as e:
            Utils.print_error(e)
            self.finalize(files_dests)
            return

        self.signals_.value_changed.emit(0)

        for file_path in self.files:

            if not self.is_should_run():
                break

            dest_path = os.path.join(self.dest, os.path.basename(file_path))
            files_dests.append(dest_path)

            try:
                with open(file_path, 'rb') as fsrc, open(dest_path, 'wb') as fdest:
                    while self.is_should_run():
                        buf = fsrc.read(1024*1024)
                        if not buf:
                            break
                        fdest.write(buf)
                        copied_size += len(buf)
                        percent = int((copied_size / total_size) * 100)
                        self.signals_.value_changed.emit(percent)
                if self.move_files:
                    os.remove(file_path)
            except Exception as e:
                Utils.print_error(e)
                break
        
        self.finalize(files_dests)

    def stop_cmd(self):
        self.set_should_run(False)

    def finalize(self, files_dests: list[str]):
        try:
            self.signals_.value_changed.emit(100)
        except RuntimeError:
            ...
        self.signals_.finished_.emit(files_dests)
        CopyFiles.list_of_file_lists.append(files_dests)
        CopyFiles.current_threads.remove(self)


class FavSignals(QObject):
    finished_ = pyqtSignal(int)


class FavTask(URunnable):
    def __init__(self, rel_img_path: str, value: int):
        super().__init__()
        self.signals_ = FavSignals()
        self.rel_img_path = rel_img_path
        self.value = value

    def task(self):
        values = {"fav": self.value}
        q = update(THUMBS)
        q = q.where(THUMBS.c.short_src == self.rel_img_path)
        q = q.where(THUMBS.c.brand == MainFolder.current.name)
        q = q.values(**values)

        conn = Dbase.engine.connect()

        try:
            conn.execute(q)
            conn.commit()
            self.signals_.finished_.emit(self.value)
        except Exception as e:
            Utils.print_error(e)
            conn.rollback()

        conn.close()