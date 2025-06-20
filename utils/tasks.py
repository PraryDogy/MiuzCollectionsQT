import gc
import os

from PyQt5.QtCore import QObject, QRunnable, QThreadPool, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QPixmap, QPixmapCache
from sqlalchemy import select, update

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


class CopyFilesTask(URunnable):
    current_threads: list["CopyFilesTask"] = []
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
        CopyFilesTask.current_threads.append(self)
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
        CopyFilesTask.list_of_file_lists.append(files_dests)
        CopyFilesTask.current_threads.remove(self)


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


class MenuSignals(QObject):
    finished_ = pyqtSignal(list)


class LoadCollectionsTask(URunnable):
    def __init__(self, main_folder: MainFolder):
        super().__init__()
        self.main_folder = main_folder
        self.signals_ = MenuSignals()

    def task(self) -> None:
        menus = self.get_collections_list()
        try:
            self.signals_.finished_.emit(menus)
        except RuntimeError as e:
            Utils.print_error(e)

    def get_collections_list(self) -> list[dict]:
        """
        Queries the database to load distinct `THUMBS.c.coll`, processes them, 
        and returns a list of dictionaries containing short and full `THUMBS.c.coll`.

        :return: A sorted list of dictionaries with `short_name` and `coll_name` keys.
        """

        conn = Dbase.engine.connect()
        q = select(THUMBS.c.coll)
        q = q.where(THUMBS.c.brand == self.main_folder.name)
        q = q.distinct()
        res = conn.execute(q).fetchall()
        conn.close()

        if not res:
            return list()

        menus: list[dict] = []

        for row in res:
            coll_name: str = row[0]
            fake_name = coll_name.lstrip("0123456789").strip()
            fake_name = fake_name if fake_name else coll_name
            menus.append(
                {
                    "short_name": fake_name,
                    "coll_name": coll_name
                }
            )
        return sorted(menus, key = lambda x: x["short_name"])
    

class LoadImageSignals(QObject):
    finished_ = pyqtSignal(tuple)


class LoadThumb(URunnable):
    def __init__(self, rel_img_path: str):
        """
        Возвращает в сигнале finished_ (rel_img_path, QPixmap)
        """
        super().__init__()
        self.signals_ = LoadImageSignals()
        self.rel_img_path = rel_img_path

    def task(self):
        conn = Dbase.engine.connect()
        q = select(THUMBS.c.short_hash) #rel thumb path
        q = q.where(THUMBS.c.short_src == self.rel_img_path)
        q = q.where(THUMBS.c.brand == MainFolder.current.name)
        rel_thumb_path = conn.execute(q).scalar()
        conn.close()

        if rel_thumb_path:
            thumb_path = Utils.get_thumb_path(rel_thumb_path)
            thumb = Utils.read_thumb(thumb_path)
            thumb = Utils.desaturate_image(thumb, 0.2)
            pixmap = Utils.pixmap_from_array(thumb)
        else:
            pixmap = QPixmap(1, 1)
            pixmap.fill(QColor(128, 128, 128))

        image_data = (self.rel_img_path, pixmap)
        self.signals_.finished_.emit(image_data)


class LoadImage(URunnable):
    max_images_count = 50

    def __init__(self, img_path: str, cached_images: dict[str, QPixmap]):
        """
        Возвращает в сигнале finished_ (img_path, QPixmap)
        """
        super().__init__()
        self.signals_ = LoadImageSignals()
        self.img_path = img_path
        self.cached_images = cached_images

    def task(self):
        if self.img_path not in self.cached_images:
            img = Utils.read_image(self.img_path)
            if img is not None:
                img = Utils.desaturate_image(img, 0.2)
                self.pixmap = Utils.pixmap_from_array(img)
                self.cached_images[self.img_path] = self.pixmap
        else:
            self.pixmap = self.cached_images.get(self.img_path)

        if not hasattr(self, "pixmap"):
            print("не могу загрузить крупное изображение")
            self.pixmap = QPixmap(0, 0)

        if len(self.cached_images) > self.max_images_count:
            self.cached_images.pop(next(iter(self.cached_images)))

        image_data = (self.img_path, self.pixmap)

        try:
            self.signals_.finished_.emit(image_data)
        except RuntimeError:
            ...

        # === очищаем ссылки
        del self.pixmap
        self.signals_ = None
        gc.collect()
        QPixmapCache.clear()