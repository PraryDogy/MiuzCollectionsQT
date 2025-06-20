import gc
import os
import subprocess

from PyQt5.QtCore import QObject, QRunnable, QThreadPool, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QPixmap, QPixmapCache
from sqlalchemy import select, update

from database import THUMBS, Dbase
from lang import Lang
from main_folder import MainFolder
from signals import SignalsApp

from .scaner import (Compator, DbImages, DbUpdater, FileUpdater, FinderImages,
                     MainFolderRemover)
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




class ImgInfoSignals(QObject):
    finished_ = pyqtSignal(dict)
    delayed_info = pyqtSignal(str)


class SingleImgInfo(URunnable):
    max_row = 50

    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.signals_ = ImgInfoSignals()

    def task(self):
        mail_folder_path = MainFolder.current.is_available()
        try:
            name = os.path.basename(self.url)
            _, type_ = os.path.splitext(name)
            stats = os.stat(self.url)
            size = Utils.get_f_size(stats.st_size)
            mod = Utils.get_f_date(stats.st_mtime)
            coll = Utils.get_coll_name(mail_folder_path, self.url)
            thumb_path = Utils.create_thumb_path(self.url)

            res = {
                Lang.file_name: self.lined_text(name),
                Lang.type_: type_,
                Lang.file_size: size,
                Lang.place: self.lined_text(self.url),
                Lang.thumb_path: self.lined_text(thumb_path),
                Lang.changed: mod,
                Lang.collection: self.lined_text(coll),
                Lang.resol: Lang.calculating,
                }
            
            self.signals_.finished_.emit(res)

            res = self.get_img_resol(self.url)
            if res:
                self.signals_.delayed_info.emit(res)
        
        except Exception as e:
            Utils.print_error(e)
            res = {
                Lang.file_name: self.lined_text(os.path.basename(self.url)),
                Lang.place: self.lined_text(self.url),
                Lang.type_: self.lined_text(os.path.splitext(self.url)[0])
                }
            self.signals_.finished_.emit(res)

    def get_img_resol(self, img_path: str):
        img_ = Utils.read_image(img_path)
        if img_ is not None and len(img_.shape) > 1:
            h, w = img_.shape[0], img_.shape[1]
            return f"{w}x{h}"
        else:
            return ""

    def lined_text(self, text: str):
        if len(text) > self.max_row:
            text = [
                text[i:i + self.max_row]
                for i in range(0, len(text), self.max_row)
                ]
            return "\n".join(text)
        else:
            return text


class MultipleImgInfo(URunnable):
    max_row = 50

    def __init__(self, img_path_list: list[str]):
        super().__init__()
        self.img_path_list = img_path_list
        self.signals_ = ImgInfoSignals()
    
    def task(self):
        names = [
            os.path.basename(i)
            for i in self.img_path_list
        ]
        names = names[:10]
        names = ", ".join(names)
        names = self.lined_text(names)
        if len(self.img_path_list) > 10:
            names = names + ", ..."

        res = {
            Lang.file_name: names,
            Lang.total: str(len(self.img_path_list)),
            Lang.file_size: self.get_total_size()
        }
        self.signals_.finished_.emit(res)

    def get_total_size(self):
        total = 0
        for i in self.img_path_list:
            stats = os.stat(i)
            size_ = stats.st_size
            total += size_

        return Utils.get_f_size(total)

    def lined_text(self, text: str):
        if len(text) > self.max_row:
            text = [
                text[i:i + self.max_row]
                for i in range(0, len(text), self.max_row)
                ]
            return "\n".join(text)
        else:
            return text


class RemoveFilesSignals(QObject):
    finished_ = pyqtSignal()


class RemoveFilesTask(URunnable):
    scpt = os.path.join("scripts", "remove_files.scpt")

    def __init__(self, img_path_list: list[str]):
        """
        Удаляет изображения из hashdir
        Удаляет записи об изображениях из бд
        """
        super().__init__()
        self.signals_ = RemoveFilesSignals()
        self.img_path_list = img_path_list

    def task(self):
        try:
            self.remove_thumbs()
            command = ["osascript", self.scpt] + self.img_path_list
            subprocess.run(command)
        except Exception as e:
            Utils.print_error(e)
        try:
            self.signals_.finished_.emit()
        except RuntimeError as e:
            Utils.print_error(e)

    def remove_thumbs(self):      
        thumb_path_list = [
            Utils.create_thumb_path(img_path)
            for img_path in self.img_path_list
        ]
        rel_thumb_path_list = [
            Utils.get_rel_thumb_path(thumb_path)
            for thumb_path in thumb_path_list
        ]

        main_folder = MainFolder.current
        
        # new_items пустой так как мы только удаляем thumbs из hashdir
        file_updater = FileUpdater(rel_thumb_path_list, [], main_folder)
        del_items, new_items = file_updater.run()
        
        # new_items пустой так как мы только удаляем thumbs из бд
        db_updater = DbUpdater(del_items, [], main_folder)
        db_updater.run()


class UploadFilesSignals(QObject):
    finished_ = pyqtSignal()


class UploadFilesTask(URunnable):
    def __init__(self, img_path_list: list):
        """
        Записывает на диск в hashdir изображения
        Делает записи в бд о загруженных изображениях
        """
        super().__init__()
        self.img_path_list = img_path_list
        self.signals_ = UploadFilesSignals()

    def task(self):
        img_with_stats_list = []
        for img_path in self.img_path_list:
            try:
                stat = os.stat(img_path)
            except Exception as e:
                Utils.print_error(e)
                continue
            size, birth, mod = stat.st_size, stat.st_birthtime, stat.st_mtime
            data = (img_path, size, birth, mod)
            img_with_stats_list.append(data)
        # del_items пустой, так как нас интересует только добавление в БД
        file_updater = FileUpdater([], img_with_stats_list, MainFolder.current)
        del_items, new_items = file_updater.run()
        # del_items пустой, так как нас интересуют только новые изображения
        db_updater = DbUpdater([], new_items, MainFolder.current)
        db_updater.run()
        try:
            self.signals_.finished_.emit()
        except RuntimeError as e:
            Utils.print_error(e)


class ScanerSignals(QObject):
    finished_ = pyqtSignal()


class ScanerTask(URunnable):
    def __init__(self):
        super().__init__()
        self.signals_ = ScanerSignals()
        self.can_scan = True

    def task(self):
        for main_folder in MainFolder.list_:
            if main_folder.is_available():
                self.main_folder_scan(main_folder)
                print("scaner started", main_folder.name)

    def main_folder_scan(self, main_folder: MainFolder):
        main_folder_remover = MainFolderRemover()
        main_folder_remover.run()
        finder_images = FinderImages(main_folder, self.can_scan)
        finder_images = finder_images.run()
        gc.collect()
        if isinstance(finder_images, list):
            db_images = DbImages(main_folder)
            db_images = db_images.run()
            compator = Compator(finder_images, db_images)
            del_items, new_items = compator.run()
            file_updater = FileUpdater(del_items, new_items, main_folder)
            del_items, new_items = file_updater.run()
            db_updater = DbUpdater(del_items, new_items, main_folder)
            db_updater.run()
        try:
            self.signals_.finished_.emit()
        except RuntimeError:
            pass